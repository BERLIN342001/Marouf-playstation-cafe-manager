import flet as ft
from datetime import datetime
from database.db import SessionLocal
from services.services import (
    create_employee, get_employees, get_employee_by_id,
    update_employee, delete_employee, check_in, check_out,
    get_attendance
)
from ui.components.widgets import (
    AppColors, PageTemplate, show_snackbar, make_search_field,
    make_confirm_dialog, make_text_field, make_dropdown,
    format_currency, format_datetime, get_role_label, get_shift_label
)


class EmployeesPage(PageTemplate):
    def __init__(self, page):
        super().__init__(page, "إدارة الموظفين")

    def build_content(self):
        self.employees_list = ft.Column(spacing=8)
        self.attendance_list = ft.Column(spacing=6)
        self.tabs = ft.Tabs(
            selected_index=0,
            on_change=self.on_tab_change,
            tabs=[
                ft.Tab(text="الموظفين", icon=ft.icons.PEOPLE),
                ft.Tab(text="الحضور", icon=ft.icons.ACCESS_TIME),
            ],
        )
        return ft.Column(
            controls=[
                self.tabs,
                ft.Container(height=10),
                ft.Container(content=self.employees_list, expand=True),
                ft.Container(content=self.attendance_list, expand=True),
            ],
            spacing=0, expand=True,
        )

    def on_tab_change(self, e):
        self.refresh()

    def refresh(self):
        db = SessionLocal()
        try:
            tab = self.tabs.selected_index
            if tab == 0:
                self.employees_list.visible = True
                self.attendance_list.visible = False
                self._refresh_employees(db)
            else:
                self.employees_list.visible = False
                self.attendance_list.visible = True
                self._refresh_attendance(db)
            self.update()
        finally:
            db.close()

    def _refresh_employees(self, db):
        employees = get_employees(db)
        items = []
        for emp in employees:
            items.append(ft.Card(elevation=1, margin=ft.margin.only(bottom=6),
                content=ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.icons.BADGE, size=24, color=ft.colors.WHITE),
                            width=48, height=48, bgcolor=AppColors.INFO,
                            border_radius=12, alignment=ft.alignment.center,
                        ),
                        ft.Column([
                            ft.Text(emp.name, size=15, weight=ft.FontWeight.W_600, color=AppColors.TEXT),
                            ft.Text(emp.phone, size=12, color=AppColors.TEXT_SECONDARY),
                        ], spacing=1, expand=True),
                        ft.Column([
                            ft.Text(get_role_label(emp.role), size=12, color=AppColors.PRIMARY),
                            ft.Text(get_shift_label(emp.shift), size=12, color=AppColors.TEXT_SECONDARY),
                            ft.Text(format_currency(emp.salary), size=12, color=AppColors.SUCCESS),
                        ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.END),
                        ft.Column([
                            ft.IconButton(icon=ft.icons.EDIT, size=18,
                                          on_click=lambda e, eid=emp.id: self.show_form_dialog(eid)),
                            ft.IconButton(icon=ft.icons.DELETE, size=18, icon_color=AppColors.DANGER,
                                          on_click=lambda e, eid=emp.id: self.confirm_delete(eid)),
                        ], spacing=0),
                    ], spacing=12),
                    padding=12)))
        if not items:
            items = [ft.Container(content=ft.Text("لا يوجد موظفين", size=15,
                color=AppColors.TEXT_SECONDARY),
                padding=40, alignment=ft.alignment.center, expand=True)]
        self.employees_list.controls = items

    def _refresh_attendance(self, db):
        records = get_attendance(db)
        items = []
        for r in records[:50]:
            emp = r.employee
            name = emp.name if emp else f"موظف #{r.employee_id}"
            check_out_str = format_datetime(r.check_out) if r.check_out else "لم يسجل خروج"
            items.append(ft.Card(elevation=1, margin=ft.margin.only(bottom=4),
                content=ft.Container(
                    content=ft.Row([
                        ft.Text(name, size=13, weight=ft.FontWeight.W_500, color=AppColors.TEXT, expand=True),
                        ft.Text(format_datetime(r.check_in), size=12, color=AppColors.SUCCESS),
                        ft.Text("→", size=12, color=AppColors.TEXT_SECONDARY),
                        ft.Text(check_out_str, size=12,
                                color=AppColors.DANGER if not r.check_out else AppColors.TEXT),
                    ], spacing=10),
                    padding=10)))
        if not items:
            items = [ft.Container(content=ft.Text("لا توجد سجلات", size=15,
                color=AppColors.TEXT_SECONDARY),
                padding=40, alignment=ft.alignment.center, expand=True)]
        self.attendance_list.controls = items

    def show_form_dialog(self, emp_id=None):
        db = SessionLocal()
        try:
            is_edit = emp_id is not None
            emp = get_employee_by_id(db, emp_id) if is_edit else None
            name_f = make_text_field("الاسم", emp.name if is_edit else "")
            phone_f = make_text_field("رقم التليفون", emp.phone if is_edit else "")
            role_dd = make_dropdown("الوظيفة", [
                ("admin", "مدير"), ("cashier", "كاشير"), ("supervisor", "مشرف")
            ], emp.role if is_edit else "cashier")
            shift_dd = make_dropdown("الوردية", [
                ("morning", "صباحي"), ("evening", "مسائي"), ("night", "ليلي")
            ], emp.shift if is_edit else "morning")
            salary_f = make_text_field("الراتب", str(emp.salary) if is_edit else "0")

            def save(e):
                db2 = SessionLocal()
                try:
                    data = {"name": name_f.value, "phone": phone_f.value,
                            "role": role_dd.value, "shift": shift_dd.value,
                            "salary": float(salary_f.value or 0)}
                    if is_edit:
                        update_employee(db2, emp_id, **data)
                    else:
                        create_employee(db2, **data)
                    dlg.open = False
                    self.page.update()
                    self.refresh()
                    show_snackbar(self.page, "تم الحفظ", AppColors.SUCCESS)
                except Exception as ex:
                    show_snackbar(self.page, str(ex), AppColors.DANGER)
                finally:
                    db2.close()

            dlg = ft.AlertDialog(
                title=ft.Text("تعديل موظف" if is_edit else "إضافة موظف",
                              ),
                content=ft.Column([name_f, phone_f, ft.Row([role_dd, shift_dd], spacing=12), salary_f],
                                  spacing=12, width=420),
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

    def confirm_delete(self, emp_id):
        dlg = make_confirm_dialog("حذف الموظف", "هل أنت متأكد؟",
                                  lambda: self._do_delete(emp_id), self.page)
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _do_delete(self, emp_id):
        db = SessionLocal()
        try:
            delete_employee(db, emp_id)
            self.refresh()
            show_snackbar(self.page, "تم الحذف", AppColors.DANGER)
        finally:
            db.close()