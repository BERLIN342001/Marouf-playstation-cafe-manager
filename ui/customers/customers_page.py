import flet as ft
from database.db import SessionLocal
from services.services import (
    create_customer, get_customers, get_customer_by_id,
    update_customer, delete_customer, charge_customer_balance
)
from ui.components.widgets import (
    AppColors, PageTemplate, show_snackbar, make_search_field,
    make_confirm_dialog, make_form_field, make_text_field,
    format_currency, format_datetime
)


class CustomersPage(PageTemplate):
    def __init__(self, page):
        super().__init__(page, "إدارة العملاء")

    def build_content(self):
        self.search_field = make_search_field(on_change=self.on_search, placeholder="ابحث بالاسم أو الرقم...")
        self.customers_list = ft.Column(spacing=8)
        return ft.Column(
            controls=[
                ft.Row([
                    self.search_field,
                    ft.ElevatedButton("إضافة عميل", icon=ft.icons.PERSON_ADD,
                        on_click=lambda e: self.show_form_dialog(),
                        style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY,
                                             shape=ft.RoundedRectangleBorder(radius=10))),
                ], spacing=12),
                ft.Container(height=10),
                ft.Container(content=self.customers_list, expand=True),
            ],
            spacing=0, expand=True,
        )

    def on_search(self, e):
        self.refresh(e.control.value)

    def refresh(self, search=""):
        db = SessionLocal()
        try:
            customers = get_customers(db, search=search)
            if not customers:
                self.customers_list.controls = [
                    ft.Container(content=ft.Text("لا يوجد عملاء", size=15,
                        color=AppColors.TEXT_SECONDARY),
                        padding=40, alignment=ft.alignment.center, expand=True)
                ]
            else:
                items = []
                for c in customers:
                    items.append(ft.Card(elevation=1, margin=ft.margin.only(bottom=6),
                        content=ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Icon(ft.icons.PERSON, size=24, color=ft.colors.WHITE),
                                    width=48, height=48, bgcolor=AppColors.PRIMARY,
                                    border_radius=12, alignment=ft.alignment.center,
                                ),
                                ft.Column([
                                    ft.Text(c.name, size=15, weight=ft.FontWeight.W_600, color=AppColors.TEXT),
                                    ft.Text(c.phone, size=13, color=AppColors.TEXT_SECONDARY),
                                ], spacing=2, expand=True),
                                ft.Column([
                                    ft.Text(f"الرصيد: {format_currency(c.balance)}", size=13,
                                            color=AppColors.PRIMARY),
                                    ft.Text(f"النقاط: {c.points}", size=12,
                                            color=AppColors.WARNING),
                                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                                ft.Column([
                                    ft.IconButton(icon=ft.icons.EDIT, size=20,
                                        on_click=lambda e, cid=c.id: self.show_form_dialog(cid)),
                                    ft.IconButton(icon=ft.icons.DELETE, size=20, icon_color=AppColors.DANGER,
                                        on_click=lambda e, cid=c.id: self.confirm_delete(cid)),
                                    ft.IconButton(icon=ft.icons.ACCOUNT_BALANCE_WALLET, size=20,
                                        icon_color=AppColors.SUCCESS,
                                        on_click=lambda e, cid=c.id: self.show_charge_dialog(cid)),
                                ], spacing=0),
                            ], spacing=12),
                            padding=15)))
                self.customers_list.controls = items
            self.update()
        finally:
            db.close()

    def show_form_dialog(self, customer_id=None):
        db = SessionLocal()
        try:
            is_edit = customer_id is not None
            customer = get_customer_by_id(db, customer_id) if is_edit else None

            name_f = make_text_field("الاسم", customer.name if is_edit else "")
            phone_f = make_text_field("رقم التليفون", customer.phone if is_edit else "")
            age_f = make_text_field("العمر", str(customer.age) if is_edit and customer.age else "")
            notes_f = make_text_field("ملاحظات", customer.notes if is_edit else "", expand=True)

            def save(e):
                db2 = SessionLocal()
                try:
                    data = {
                        "name": name_f.value, "phone": phone_f.value,
                        "age": int(age_f.value) if age_f.value else None,
                        "notes": notes_f.value or None
                    }
                    if is_edit:
                        update_customer(db2, customer_id, **data)
                    else:
                        create_customer(db2, **data)
                    dlg.open = False
                    self.page.update()
                    self.refresh()
                    show_snackbar(self.page, "تم الحفظ بنجاح", AppColors.SUCCESS)
                except Exception as ex:
                    show_snackbar(self.page, str(ex), AppColors.DANGER)
                finally:
                    db2.close()

            dlg = ft.AlertDialog(
                title=ft.Text("تعديل عميل" if is_edit else "إضافة عميل جديد",
                              ),
                content=ft.Column([name_f, phone_f, age_f, notes_f], spacing=12, width=420),
                actions=[
                    ft.TextButton("إلغاء", on_click=lambda e: close(e)),
                    ft.ElevatedButton("حفظ", on_click=save,
                                      style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY,
                                                           shape=ft.RoundedRectangleBorder(radius=10))),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            def close(e):
                dlg.open = False
                self.page.update()

            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()
        finally:
            db.close()

    def show_charge_dialog(self, customer_id):
        db = SessionLocal()
        try:
            customer = get_customer_by_id(db, customer_id)
            if not customer:
                return

            amount_f = make_text_field("مبلغ الشحن", "100")
            info = ft.Text(f"الرصيد الحالي: {format_currency(customer.balance)}",
                          size=14, color=AppColors.TEXT)

            def save(e):
                db2 = SessionLocal()
                try:
                    amt = float(amount_f.value or 0)
                    charge_customer_balance(db2, customer_id, amt)
                    dlg.open = False
                    self.page.update()
                    self.refresh()
                    show_snackbar(self.page, f"تم شحن {format_currency(amt)} بنجاح", AppColors.SUCCESS)
                except Exception as ex:
                    show_snackbar(self.page, str(ex), AppColors.DANGER)
                finally:
                    db2.close()

            dlg = ft.AlertDialog(
                title=ft.Text(f"شحن رصيد - {customer.name}",
                              ),
                content=ft.Column([info, amount_f], spacing=12, width=350),
                actions=[
                    ft.TextButton("إلغاء", on_click=lambda e: close(e)),
                    ft.ElevatedButton("شحن", on_click=save,
                                      style=ft.ButtonStyle(bgcolor=AppColors.SUCCESS,
                                                           shape=ft.RoundedRectangleBorder(radius=10))),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            def close(e):
                dlg.open = False
                self.page.update()

            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()
        finally:
            db.close()

    def confirm_delete(self, customer_id):
        dlg = make_confirm_dialog(
            "حذف العميل", "هل أنت متأكد من حذف هذا العميل؟",
            lambda: self._do_delete(customer_id), self.page)
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _do_delete(self, customer_id):
        db = SessionLocal()
        try:
            delete_customer(db, customer_id)
            self.refresh()
            show_snackbar(self.page, "تم حذف العميل", AppColors.DANGER)
        finally:
            db.close()