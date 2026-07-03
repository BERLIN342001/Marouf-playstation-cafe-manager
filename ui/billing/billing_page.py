import flet as ft
from datetime import datetime
from database.db import SessionLocal
from services.services import get_payments, get_daily_revenue
from ui.components.widgets import (
    AppColors, PageTemplate, show_snackbar, format_currency,
    format_datetime, get_payment_label, make_form_field,
    make_text_field, make_dropdown, make_search_field
)


class BillingPage(PageTemplate):
    def __init__(self, page):
        super().__init__(page, "الفواتير والمحاسبة")

    def build_content(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.date_field = ft.TextField(
            label="التاريخ (YYYY-MM-DD)",
            value=today_str,
            border_radius=10,
            filled=True,
            width=200,
        )
        self.total_text = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=AppColors.PRIMARY)
        self.payments_list = ft.Column(spacing=6)
        return ft.Column(
            controls=[
                ft.Row([
                    ft.Column([
                        ft.Text("ملخص اليوم", size=16, weight=ft.FontWeight.BOLD),
                        self.total_text,
                    ], spacing=4),
                    ft.Container(expand=True),
                    self.date_field,
                ]),
                ft.Container(height=15),
                ft.Text("سجل المدفوعات", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                ft.Container(content=self.payments_list, expand=True),
            ],
            spacing=0, expand=True,
        )

    def refresh(self, e=None):
        db = SessionLocal()
        try:
            date_str = self.date_field.value
            try:
                sel_date = datetime.strptime(date_str, "%Y-%m-%d")
            except (ValueError, TypeError):
                sel_date = datetime.now()
            total, payments = get_daily_revenue(db, sel_date)
            self.total_text.value = f"الإجمالي: {format_currency(total)}"

            if not payments:
                self.payments_list.controls = [
                    ft.Container(content=ft.Text("لا توجد مدفوعات في هذا اليوم", size=15,
                        color=AppColors.TEXT_SECONDARY),
                        padding=40, alignment=ft.alignment.center, expand=True)
                ]
            else:
                items = []
                for p in payments:
                    cust_name = p.customer.name if p.customer else "زائر"
                    st_name = f"جلسة #{p.session_id}" if p.session_id else "شحن رصيد"
                    items.append(
                        ft.Card(elevation=1, margin=ft.margin.only(bottom=4),
                            content=ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.RECEIPT, size=20, color=AppColors.PRIMARY),
                                    ft.Column([
                                        ft.Text(f"{cust_name} - {st_name}", size=13,
                                                weight=ft.FontWeight.W_500, color=AppColors.TEXT),
                                        ft.Text(get_payment_label(p.payment_method), size=11,
                                                color=AppColors.TEXT_SECONDARY),
                                    ], spacing=1, expand=True),
                                    ft.Column([
                                        ft.Text(format_currency(p.final_amount), size=14,
                                                weight=ft.FontWeight.BOLD, color=AppColors.TEXT),
                                        ft.Text(f"خصم: {format_currency(p.discount)}", size=11,
                                                color=AppColors.DANGER),
                                    ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.END),
                                    ft.Text(format_datetime(p.created_at), size=11,
                                            color=AppColors.TEXT_SECONDARY),
                                ], spacing=10),
                                padding=12))
                    )
                self.payments_list.controls = items
            self.update()
        finally:
            db.close()