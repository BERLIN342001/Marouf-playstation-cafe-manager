import customtkinter as ctk
from tkinter import messagebox
from main import *
from database.db import SessionLocal
from services.services import (
    create_employee, get_employees, get_employee_by_id,
    update_employee, delete_employee, get_attendance
)
from datetime import datetime
from utils.helpers import get_role_label, get_shift_label


class EmployeeDialog(ctk.CTkToplevel):
    def __init__(self, parent, employee=None):
        super().__init__(parent)
        self.title("تعديل موظف" if employee else "إضافة موظف")
        self.geometry("420x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result = None
        self.employee = employee

        self._build()
        if employee:
            self.name_e.insert(0, employee.name)
            self.phone_e.insert(0, employee.phone)
            self.role_cb.set({"admin": "مدير", "cashier": "كاشير", "supervisor": "مشرف"}.get(employee.role, employee.role))
            self.shift_cb.set({"morning": "صباحي", "evening": "مسائي", "night": "ليلي"}.get(employee.shift, employee.shift))
            self.salary_e.insert(0, str(employee.salary))

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _build(self):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(f, text="الاسم", font=("Segoe UI", 12), anchor="e").pack(fill="x", pady=(5, 0))
        self.name_e = ctk.CTkEntry(f, corner_radius=8)
        self.name_e.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(f, text="رقم التليفون", font=("Segoe UI", 12), anchor="e").pack(fill="x", pady=(5, 0))
        self.phone_e = ctk.CTkEntry(f, corner_radius=8)
        self.phone_e.pack(fill="x", pady=(0, 5))

        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", pady=5)
        ctk.CTkLabel(row, text="الوظيفة", font=("Segoe UI", 12)).pack(side="right", padx=(0, 5))
        self.role_cb = ctk.CTkComboBox(row, values=["كاشير", "مشرف", "مدير"], corner_radius=8, width=150)
        self.role_cb.set("كاشير")
        self.role_cb.pack(side="left", padx=(5, 0))

        ctk.CTkLabel(f, text="الوردية", font=("Segoe UI", 12), anchor="e").pack(fill="x", pady=(5, 0))
        self.shift_cb = ctk.CTkComboBox(f, values=["صباحي", "مسائي", "ليلي"], corner_radius=8)
        self.shift_cb.set("صباحي")
        self.shift_cb.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(f, text="الراتب", font=("Segoe UI", 12), anchor="e").pack(fill="x", pady=(5, 0))
        self.salary_e = ctk.CTkEntry(f, corner_radius=8)
        self.salary_e.pack(fill="x", pady=(0, 10))

        btn_row = ctk.CTkFrame(f, fg_color="transparent")
        btn_row.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(btn_row, text="حفظ", fg_color=PRIMARY, corner_radius=8, width=100,
                       command=self._save).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="إلغاء", fg_color=TEXT_SEC, corner_radius=8, width=100,
                       command=self.destroy).pack(side="left", padx=5)

    def _save(self):
        role_map = {"كاشير": "cashier", "مشرف": "supervisor", "مدير": "admin"}
        shift_map = {"صباحي": "morning", "مسائي": "evening", "ليلي": "night"}
        self.result = {
            "name": self.name_e.get(), "phone": self.phone_e.get(),
            "role": role_map.get(self.role_cb.get(), "cashier"),
            "shift": shift_map.get(self.shift_cb.get(), "morning"),
            "salary": float(self.salary_e.get() or 0),
        }
        self.destroy()


class EmployeesPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, app, "إدارة الموظفين")
        self.tab = 0

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
        toolbar.pack(fill="x", pady=(0, 10))

        seg = ctk.CTkSegmentedButton(toolbar, values=["الموظفين", "الحضور"],
                                      command=self._on_tab, font=("Segoe UI", 13))
        seg.set("الموظفين")
        seg.pack(side="right", padx=10, pady=10)

        ctk.CTkButton(toolbar, text="➕ إضافة موظف", fg_color=PRIMARY, corner_radius=8,
                       command=self._add).pack(side="left", padx=10, pady=10)

        if self.tab == 0:
            self._show_employees()
        else:
            self._show_attendance()

    def _on_tab(self, val):
        self.tab = 0 if val == "الموظفين" else 1
        self.refresh()

    def _show_employees(self):
        db = SessionLocal()
        try:
            employees = get_employees(db)
            if not employees:
                ctk.CTkLabel(self, text="لا يوجد موظفين", font=("Segoe UI", 15), text_color=TEXT_SEC).pack(pady=40)
                return

            for emp in employees:
                card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
                card.pack(fill="x", pady=3)

                info = ctk.CTkFrame(card, fg_color="transparent")
                info.pack(side="right", fill="both", expand=True, padx=15, pady=10)

                ctk.CTkLabel(info, text=emp.name, font=("Segoe UI", 15, "bold"), text_color=TEXT, anchor="e").pack(fill="x")
                ctk.CTkLabel(info, text=emp.phone, font=("Segoe UI", 12), text_color=TEXT_SEC, anchor="e").pack(fill="x")

                details = ctk.CTkFrame(card, fg_color="transparent")
                details.pack(side="right", padx=15, pady=10)

                ctk.CTkLabel(details, text=get_role_label(emp.role), font=("Segoe UI", 12), text_color=PRIMARY).pack(anchor="w")
                ctk.CTkLabel(details, text=get_shift_label(emp.shift), font=("Segoe UI", 11), text_color=TEXT_SEC).pack(anchor="w")
                ctk.CTkLabel(details, text=fc(emp.salary), font=("Segoe UI", 12), text_color=SUCCESS).pack(anchor="w")

                btns = ctk.CTkFrame(card, fg_color="transparent")
                btns.pack(side="left", padx=10, pady=10)
                ctk.CTkButton(btns, text="✏️", width=35, corner_radius=8,
                               command=lambda e=emp: self._edit(e)).pack(side="left", padx=2)
                ctk.CTkButton(btns, text="🗑️", width=35, fg_color=DANGER, corner_radius=8,
                               command=lambda eid=emp.id: self._delete(eid)).pack(side="left", padx=2)
        finally:
            db.close()

    def _show_attendance(self):
        db = SessionLocal()
        try:
            records = get_attendance(db)
            if not records:
                ctk.CTkLabel(self, text="لا توجد سجلات", font=("Segoe UI", 15), text_color=TEXT_SEC).pack(pady=40)
                return

            header = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=8)
            header.pack(fill="x", pady=(0, 5))
            ctk.CTkLabel(header, text="الموظف", font=("Segoe UI", 12, "bold"), anchor="e", width=200).pack(side="right", padx=10, pady=8)
            ctk.CTkLabel(header, text="تسجيل دخول", font=("Segoe UI", 12, "bold"), anchor="e", width=180).pack(side="right", padx=10, pady=8)
            ctk.CTkLabel(header, text="تسجيل خروج", font=("Segoe UI", 12, "bold"), anchor="e", width=180).pack(side="right", padx=10, pady=8)

            for r in records[:50]:
                row = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=8)
                row.pack(fill="x", pady=2)
                name = r.employee.name if r.employee else f"#{r.employee_id}"
                out = fmt_dt(r.check_out) if r.check_out else "لم يسجل خروج"
                ctk.CTkLabel(row, text=name, font=("Segoe UI", 13), anchor="e", width=200).pack(side="right", padx=10, pady=6)
                ctk.CTkLabel(row, text=fmt_dt(r.check_in), font=("Segoe UI", 12), text_color=SUCCESS, anchor="e", width=180).pack(side="right", padx=10, pady=6)
                ctk.CTkLabel(row, text=out, font=("Segoe UI", 12),
                              text_color=DANGER if not r.check_out else TEXT, anchor="e", width=180).pack(side="right", padx=10, pady=6)
        finally:
            db.close()

    def _add(self):
        dlg = EmployeeDialog(self.winfo_toplevel())
        self.wait_window(dlg)
        if dlg.result and dlg.result["name"]:
            db = SessionLocal()
            try:
                create_employee(db, **dlg.result)
                self.refresh()
            finally:
                db.close()

    def _edit(self, emp):
        dlg = EmployeeDialog(self.winfo_toplevel(), emp)
        self.wait_window(dlg)
        if dlg.result and dlg.result["name"]:
            db = SessionLocal()
            try:
                update_employee(db, emp.id, **dlg.result)
                self.refresh()
            finally:
                db.close()

    def _delete(self, emp_id):
        if messagebox.askyesno("حذف", "هل أنت متأكد من حذف هذا الموظف؟"):
            db = SessionLocal()
            try:
                delete_employee(db, emp_id)
                self.refresh()
            finally:
                db.close()