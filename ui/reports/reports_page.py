import flet as ft
from database.db import SessionLocal
from services.services import (
    get_revenue_report, get_station_usage_report,
    get_payment_method_report, get_top_customers_report
)
from ui.components.widgets import (
    AppColors, PageTemplate, format_currency, get_payment_label
)


class ReportsPage(PageTemplate):
    def __init__(self, page):
        super().__init__(page, "التقارير المالية")

    def build_content(self):
        self.tabs = ft.Tabs(
            selected_index=0,
            on_change=self.on_tab_change,
            tabs=[
                ft.Tab(text="الإيرادات", icon=ft.icons.TRENDING_UP),
                ft.Tab(text="استخدام المحطات", icon=ft.icons.SPORTS_ESPORTS),
                ft.Tab(text="طرق الدفع", icon=ft.icons.PAYMENT),
                ft.Tab(text="أفضل العملاء", icon=ft.icons.PEOPLE),
            ],
        )
        self.report_content = ft.Container(expand=True, content=ft.Column(spacing=8))
        return ft.Column(controls=[self.tabs, ft.Container(height=10), self.report_content],
                         spacing=0, expand=True)

    def on_tab_change(self, e):
        self.refresh()

    def refresh(self):
        db = SessionLocal()
        try:
            tab = self.tabs.selected_index
            if tab == 0:
                self._revenue_report(db)
            elif tab == 1:
                self._station_report(db)
            elif tab == 2:
                self._payment_report(db)
            elif tab == 3:
                self._top_customers_report(db)
            self.update()
        finally:
            db.close()

    def _revenue_report(self, db):
        data = get_revenue_report(db, 30)
        total = sum(d["revenue"] for d in data)
        total_sessions = sum(d["sessions"] for d in data)

        summary = ft.Row([
            ft.Text(f"إجمالي الإيرادات (30 يوم): {format_currency(total)}",
                    size=15, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
            ft.Text(f"إجمالي الجلسات: {total_sessions}",
                    size=14, color=AppColors.TEXT_SECONDARY),
        ], spacing=20)

        # Table header
        header = ft.Container(
            content=ft.Row([
                ft.Text("التاريخ", size=13, weight=ft.FontWeight.BOLD, expand=True),
                ft.Text("الإيرادات", size=13, weight=ft.FontWeight.BOLD, width=120),
                ft.Text("جلسات", size=13, weight=ft.FontWeight.BOLD, width=80),
            ]),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=AppColors.BG,
            border_radius=ft.border_radius.only(top_left=8, top_right=8),
        )

        rows = [header]
        for d in data[-15:]:  # last 15 days
            bg = None
            if d["revenue"] > 0:
                bar_width = min(d["revenue"] / max(total / 15, 1) * 100, 100)
                bar = ft.Container(width=int(bar_width), height=4, bgcolor=AppColors.PRIMARY,
                                   border_radius=2)
            else:
                bar = ft.Container(width=0, height=4)

            rows.append(ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(d["date"], size=13, expand=True, color=AppColors.TEXT),
                        ft.Text(format_currency(d["revenue"]), size=13, width=120,
                                color=AppColors.SUCCESS if d["revenue"] > 0 else AppColors.TEXT_SECONDARY),
                        ft.Text(str(d["sessions"]), size=13, width=80, color=AppColors.TEXT),
                    ]),
                    bar,
                ], spacing=2),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border=ft.border.only(bottom=ft.BorderSide(1, AppColors.BORDER)),
            ))

        self.report_content.content = ft.Column([summary, ft.Container(height=10)] + rows, spacing=0)

    def _station_report(self, db):
        data = get_station_usage_report(db, 30)
        if not data:
            self.report_content.content = ft.Text("لا توجد بيانات", color=AppColors.TEXT_SECONDARY)
            return

        header = ft.Container(
            content=ft.Row([
                ft.Text("المحطة", size=13, weight=ft.FontWeight.BOLD, expand=True),
                ft.Text("جلسات", size=13, weight=ft.FontWeight.BOLD, width=100),
                ft.Text("ساعات", size=13, weight=ft.FontWeight.BOLD, width=100),
                ft.Text("الإيرادات", size=13, weight=ft.FontWeight.BOLD, width=120),
            ]),
            padding=12, bgcolor=AppColors.BG, border_radius=8,
        )
        rows = [header]
        for d in sorted(data, key=lambda x: x["total_revenue"], reverse=True):
            hours = round(d["total_minutes"] / 60, 1)
            rows.append(ft.Container(
                content=ft.Row([
                    ft.Text(f"محطة #{d['station_id']}", size=13, expand=True, color=AppColors.TEXT),
                    ft.Text(str(d["total_sessions"]), size=13, width=100, color=AppColors.TEXT),
                    ft.Text(f"{hours} ساعة", size=13, width=100, color=AppColors.TEXT),
                    ft.Text(format_currency(d["total_revenue"]), size=13, width=120,
                            color=AppColors.SUCCESS),
                ]),
                padding=12, border=ft.border.only(bottom=ft.BorderSide(1, AppColors.BORDER)),
            ))
        self.report_content.content = ft.Column(rows, spacing=0)

    def _payment_report(self, db):
        data = get_payment_method_report(db, 30)
        if not data:
            self.report_content.content = ft.Text("لا توجد بيانات", color=AppColors.TEXT_SECONDARY)
            return

        cards = []
        for d in sorted(data, key=lambda x: x["total"], reverse=True):
            cards.append(ft.Card(elevation=1, margin=ft.margin.only(bottom=8),
                content=ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.PAYMENT, size=24, color=AppColors.PRIMARY),
                        ft.Column([
                            ft.Text(get_payment_label(d["method"]), size=15,
                                    weight=ft.FontWeight.W_600, color=AppColors.TEXT),
                            ft.Text(f"{d['count']} عملية", size=12, color=AppColors.TEXT_SECONDARY),
                        ], spacing=1, expand=True),
                        ft.Text(format_currency(d["total"]), size=16,
                                weight=ft.FontWeight.BOLD, color=AppColors.SUCCESS),
                    ], spacing=12),
                    padding=15)))
        self.report_content.content = ft.Column(cards, spacing=0)

    def _top_customers_report(self, db):
        data = get_top_customers_report(db, 20)
        if not data:
            self.report_content.content = ft.Text("لا توجد بيانات", color=AppColors.TEXT_SECONDARY)
            return

        items = []
        for i, d in enumerate(data):
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}"
            items.append(ft.Card(elevation=1, margin=ft.margin.only(bottom=6),
                content=ft.Container(
                    content=ft.Row([
                        ft.Text(medal, size=20, width=40, text_align=ft.TextAlign.CENTER),
                        ft.Column([
                            ft.Text(d["name"], size=14, weight=ft.FontWeight.W_600, color=AppColors.TEXT),
                            ft.Text(d["phone"], size=12, color=AppColors.TEXT_SECONDARY),
                        ], spacing=1, expand=True),
                        ft.Text(f"{d['total_sessions']} جلسة", size=12, color=AppColors.TEXT),
                        ft.Text(format_currency(d["total_spent"]), size=15,
                                weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY),
                    ], spacing=10),
                    padding=12)))
        self.report_content.content = ft.Column(items, spacing=0)