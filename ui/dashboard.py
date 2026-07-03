import flet as ft
from database.db import SessionLocal
from services.services import get_dashboard_stats, get_active_sessions
from ui.components.widgets import (
    AppColors, StatCard, PageTemplate,
    make_status_chip, format_currency, format_datetime,
    get_active_session_duration_minutes, format_duration
)


class DashboardPage(PageTemplate):
    def __init__(self, page):
        super().__init__(page, "لوحة التحكم")

    def build_content(self):
        self.stats_container = ft.Column(spacing=10)
        self.active_sessions_container = ft.Column(spacing=8)
        return self.build_body()

    def build_body(self):
        return ft.Column(
            controls=[
                # Stats Row
                ft.Row(
                    controls=[
                        ft.Column([self.stats_container], expand=True, spacing=10),
                    ],
                ),
                ft.Container(ft.Divider(color=AppColors.BORDER), height=20),
                # Active Sessions
                self.build_active_sessions_section(),
            ],
            spacing=0,
            expand=True,
        )

    def build_active_sessions_section(self):
        return ft.Column(
            controls=[
                ft.Text("الجلسات النشطة", size=18, weight=ft.FontWeight.BOLD,
                        color=AppColors.TEXT),
                ft.Container(height=10),
                self.active_sessions_container,
            ],
            spacing=0,
        )

    def refresh(self):
        db = SessionLocal()
        try:
            stats = get_dashboard_stats(db)
            active = get_active_sessions(db)

            # Build stat cards
            cards = [
                StatCard("إيرادات اليوم", format_currency(stats["today_revenue"]),
                         ft.icons.ATTACH_MONEY, AppColors.SUCCESS),
                StatCard("إيرادات الأسبوع", format_currency(stats["week_revenue"]),
                         ft.icons.TRENDING_UP, AppColors.PRIMARY),
                StatCard("محطات شغالة", f"{stats['active_sessions']} / {stats['station_stats']['total']}",
                         ft.icons.SPORTS_ESPORTS, AppColors.DANGER),
                StatCard("جلسات اليوم", str(stats["today_sessions"]),
                         ft.icons.TIMELINE, AppColors.INFO),
                StatCard("ساعات اللعب اليوم", f"{stats['today_hours']} ساعة",
                         ft.icons.SCHEDULE, AppColors.WARNING),
                StatCard("إجمالي العملاء", str(stats["total_customers"]),
                         ft.icons.PEOPLE, "#8b5cf6"),
            ]

            # Arrange cards in 3 columns
            rows = []
            for i in range(0, len(cards), 3):
                row_cards = cards[i:i+3]
                rows.append(ft.Row(
                    controls=row_cards,
                    spacing=12,
                ))

            self.stats_container.controls = rows

            # Build active sessions list
            if not active:
                self.active_sessions_container.controls = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, size=48, color=AppColors.SUCCESS),
                                ft.Text("لا توجد جلسات نشطة حالياً", size=15,
                                        color=AppColors.TEXT_SECONDARY,
                                        ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        padding=40,
                        alignment=ft.alignment.center,
                    )
                ]
            else:
                items = []
                for s in active:
                    dur = get_active_session_duration_minutes(s)
                    customer_name = s.customer.name if s.customer else "زائر"
                    station_name = s.station.name if s.station else f"محطة {s.station_id}"
                    items.append(
                        ft.Card(
                            elevation=1,
                            margin=ft.margin.only(bottom=6),
                            content=ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Container(
                                            content=ft.Text(str(s.id), size=12,
                                                            color=ft.colors.WHITE,
                                                            weight=ft.FontWeight.BOLD),
                                            width=40, height=40,
                                            bgcolor=AppColors.DANGER,
                                            border_radius=10,
                                            alignment=ft.alignment.center,
                                        ),
                                        ft.Column(
                                            controls=[
                                                ft.Text(customer_name, size=15,
                                                        weight=ft.FontWeight.W_600,
                                                        color=AppColors.TEXT),
                                                ft.Text(f"{station_name} | المدة: {format_duration(dur)}",
                                                        size=12, color=AppColors.TEXT_SECONDARY),
                                            ],
                                            spacing=2,
                                            expand=True,
                                        ),
                                        ft.Text(format_datetime(s.start_time), size=12,
                                                color=AppColors.TEXT_SECONDARY),
                                    ],
                                    spacing=12,
                                ),
                                padding=15,
                            ),
                        )
                    )
                self.active_sessions_container.controls = items

            self.update()
        finally:
            db.close()