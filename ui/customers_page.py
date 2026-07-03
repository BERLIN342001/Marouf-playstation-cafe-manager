from main import *
from database.db import SessionLocal
from services.services import (
    create_customer, get_customers, get_customer_by_id,
    update_customer, delete_customer, charge_customer_balance
)
from tkinter import messagebox


# ─── Dialog: Add / Edit Customer ────────────────────────────
class CustomerDialog(ctk.CTkToplevel):
    """نافذة إضافة / تعديل عميل"""

    def __init__(self, parent, customer=None):
        super().__init__(parent)
        self.title("تعديل عميل" if customer else "إضافة عميل جديد")
        self.geometry("420x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.customer = customer
        self.result = None

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 420) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 420) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()
        if customer:
            self._fill_data(customer)

    def _build_ui(self):
        pad = {"padx": 20, "pady": 6}

        # Title
        title = "تعديل عميل" if self.customer else "إضافة عميل جديد"
        ctk.CTkLabel(
            self, text=f"👤 {title}",
            font=("Segoe UI", 18, "bold"), text_color=TEXT
        ).pack(pady=(20, 10))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=5)

        # Name
        ctk.CTkLabel(
            form, text="الاسم:", font=("Segoe UI", 13),
            text_color=TEXT, anchor="e"
        ).grid(row=0, column=0, sticky="e", **pad)
        self.name_entry = ctk.CTkEntry(
            form, width=260, height=36,
            font=("Segoe UI", 12), placeholder_text="اسم العميل"
        )
        self.name_entry.grid(row=0, column=1, sticky="w", **pad)

        # Phone
        ctk.CTkLabel(
            form, text="رقم الهاتف:", font=("Segoe UI", 13),
            text_color=TEXT, anchor="e"
        ).grid(row=1, column=0, sticky="e", **pad)
        self.phone_entry = ctk.CTkEntry(
            form, width=260, height=36,
            font=("Segoe UI", 12), placeholder_text="01xxxxxxxxx"
        )
        self.phone_entry.grid(row=1, column=1, sticky="w", **pad)

        # Age
        ctk.CTkLabel(
            form, text="العمر:", font=("Segoe UI", 13),
            text_color=TEXT, anchor="e"
        ).grid(row=2, column=0, sticky="e", **pad)
        self.age_entry = ctk.CTkEntry(
            form, width=260, height=36,
            font=("Segoe UI", 12), placeholder_text="(اختياري)"
        )
        self.age_entry.grid(row=2, column=1, sticky="w", **pad)

        # Notes
        ctk.CTkLabel(
            form, text="ملاحظات:", font=("Segoe UI", 13),
            text_color=TEXT, anchor="e"
        ).grid(row=3, column=0, sticky="ne", **pad)
        self.notes_entry = ctk.CTkTextbox(
            form, width=260, height=80,
            font=("Segoe UI", 12)
        )
        self.notes_entry.grid(row=3, column=1, sticky="w", **pad)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(10, 20))

        ctk.CTkButton(
            btn_frame, text="إلغاء", width=120, height=38,
            font=("Segoe UI", 13), fg_color="#9ca3af", hover_color="#6b7280",
            command=self._cancel
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            btn_frame, text="💾 حفظ", width=120, height=38,
            font=("Segoe UI", 13, "bold"), fg_color=PRIMARY, hover_color="#1557b0",
            command=self._save
        ).pack(side="right", padx=8)

    def _fill_data(self, customer):
        self.name_entry.insert(0, customer.name)
        self.phone_entry.insert(0, customer.phone)
        if customer.age:
            self.age_entry.insert(0, str(customer.age))
        if customer.notes:
            self.notes_entry.insert("1.0", customer.notes)

    def _cancel(self):
        self.result = None
        self.destroy()

    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("تحذير", "يرجى إدخال اسم العميل", parent=self)
            return

        phone = self.phone_entry.get().strip()
        if not phone:
            messagebox.showwarning("تحذير", "يرجى إدخال رقم الهاتف", parent=self)
            return

        age = None
        age_text = self.age_entry.get().strip()
        if age_text:
            try:
                age = int(age_text)
            except ValueError:
                messagebox.showwarning("تحذير", "يرجى إدخال رقم صحيح للعمر", parent=self)
                return

        notes = self.notes_entry.get("1.0", "end").strip() or None

        self.result = {
            "name": name,
            "phone": phone,
            "age": age,
            "notes": notes,
        }
        self.destroy()


# ─── Dialog: Charge Balance ──────────────────────────────────
class ChargeDialog(ctk.CTkToplevel):
    """نافذة شحن رصيد العميل"""

    def __init__(self, parent, customer):
        super().__init__(parent)
        self.title(f"شحن رصيد - {customer.name}")
        self.geometry("400x320")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.customer = customer
        self.result = None

        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 320) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="💰 شحن الرصيد",
            font=("Segoe UI", 18, "bold"), text_color=TEXT
        ).pack(pady=(20, 10))

        # Customer info
        info = ctk.CTkFrame(self, fg_color="#f0f7ff", corner_radius=10)
        info.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(
            info, text=f"👤 {self.customer.name}",
            font=("Segoe UI", 14, "bold"), text_color=TEXT, anchor="e"
        ).pack(fill="x", padx=15, pady=(10, 2))

        self.balance_label = ctk.CTkLabel(
            info, text=f"الرصيد الحالي:  {fc(self.customer.balance)}",
            font=("Segoe UI", 14), text_color=PRIMARY, anchor="e"
        )
        self.balance_label.pack(fill="x", padx=15, pady=(2, 10))

        # Amount entry
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=5)

        ctk.CTkLabel(
            form, text="مبلغ الشحن (ج.م):",
            font=("Segoe UI", 13), text_color=TEXT, anchor="e"
        ).pack(anchor="e", pady=(10, 4))

        self.amount_entry = ctk.CTkEntry(
            form, width=300, height=42,
            font=("Segoe UI", 14), placeholder_text="0.00"
        )
        self.amount_entry.pack(anchor="e", pady=(0, 10))
        self.amount_entry.focus_set()

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(5, 20))

        ctk.CTkButton(
            btn_frame, text="إلغاء", width=120, height=38,
            font=("Segoe UI", 13), fg_color="#9ca3af", hover_color="#6b7280",
            command=self._cancel
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            btn_frame, text="💰 شحن", width=140, height=38,
            font=("Segoe UI", 13, "bold"), fg_color=SUCCESS, hover_color="#16a34a",
            command=self._save
        ).pack(side="right", padx=8)

    def _cancel(self):
        self.result = None
        self.destroy()

    def _save(self):
        amount_text = self.amount_entry.get().strip()
        if not amount_text:
            messagebox.showwarning("تحذير", "يرجى إدخال مبلغ الشحن", parent=self)
            return

        try:
            amount = float(amount_text)
        except ValueError:
            messagebox.showwarning("تحذير", "يرجى إدخال رقم صحيح", parent=self)
            return

        if amount <= 0:
            messagebox.showwarning("تحذير", "يجب أن يكون المبلغ أكبر من صفر", parent=self)
            return

        self.result = {"amount": amount}
        self.destroy()


# ─── Customer Card ───────────────────────────────────────────
class CustomerCard(ctk.CTkFrame):
    """بطاقة عميل واحد"""

    def __init__(self, master, customer, on_edit=None, on_delete=None, on_charge=None):
        super().__init__(master, fg_color=CARD_BG, corner_radius=12)
        self.customer = customer
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_charge = on_charge
        self._build()

    def _build(self):
        c = self.customer

        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(14, 4))

        ctk.CTkLabel(
            header, text=f"👤 {c.name}",
            font=("Segoe UI", 15, "bold"), text_color=TEXT, anchor="e"
        ).pack(side="right", fill="x", expand=True)

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="left")

        # Charge button
        ctk.CTkButton(
            btn_frame, text="💰", width=30, height=30, corner_radius=8,
            font=("", 13), fg_color="transparent", hover_color="#d1fae5",
            command=lambda: self.on_charge(c) if self.on_charge else None
        ).pack(side="left", padx=2)

        # Edit button
        ctk.CTkButton(
            btn_frame, text="✏️", width=30, height=30, corner_radius=8,
            font=("", 13), fg_color="transparent", hover_color="#e0e7ff",
            command=lambda: self.on_edit(c) if self.on_edit else None
        ).pack(side="left", padx=2)

        # Delete button
        ctk.CTkButton(
            btn_frame, text="🗑️", width=30, height=30, corner_radius=8,
            font=("", 13), fg_color="transparent", hover_color="#fee2e2",
            command=lambda: self.on_delete(c) if self.on_delete else None
        ).pack(side="left", padx=2)

        # Separator
        ctk.CTkFrame(self, height=1, fg_color="#e5e7eb").pack(fill="x", padx=14, pady=4)

        # Phone
        ctk.CTkLabel(
            self, text=f"📞 {c.phone}",
            font=("Segoe UI", 12), text_color=TEXT_SEC, anchor="e"
        ).pack(fill="x", padx=14, pady=2)

        # Age (if available)
        if c.age:
            ctk.CTkLabel(
                self, text=f"🎂 العمر: {c.age}",
                font=("Segoe UI", 12), text_color=TEXT_SEC, anchor="e"
            ).pack(fill="x", padx=14, pady=2)

        # Balance (blue) and Points (amber) side by side
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.pack(fill="x", padx=14, pady=(6, 14))

        ctk.CTkLabel(
            stats, text=f"💰 الرصيد: {fc(c.balance)}",
            font=("Segoe UI", 13, "bold"), text_color="#2563eb", anchor="e"
        ).pack(side="right", fill="x", expand=True)

        ctk.CTkLabel(
            stats, text=f"⭐ النقاط: {c.points}",
            font=("Segoe UI", 13, "bold"), text_color="#d97706", anchor="w"
        ).pack(side="left")


# ─── Customers Page ──────────────────────────────────────────
class CustomersPage(BasePage):
    """صفحة إدارة العملاء"""

    def __init__(self, master, app):
        super().__init__(master, app, title="العملاء")
        self.customers_list = []
        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            header, text="👥 إدارة العملاء",
            font=("Segoe UI", 22, "bold"), text_color=TEXT, anchor="e"
        ).pack(side="right")

        self.count_label = ctk.CTkLabel(
            header, text="", font=("Segoe UI", 13),
            text_color=TEXT_SEC, anchor="e"
        )
        self.count_label.pack(side="left", padx=10)

        # ── Toolbar ──
        toolbar = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        toolbar.pack(fill="x", pady=(0, 15))

        inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        # Search
        ctk.CTkLabel(
            inner, text="🔍", font=("", 16), anchor="e"
        ).pack(side="right", padx=(0, 6))

        self.search_entry = ctk.CTkEntry(
            inner, width=240, height=36, font=("Segoe UI", 12),
            placeholder_text="بحث بالاسم أو الهاتف..."
        )
        self.search_entry.pack(side="right", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self._apply_filter())

        # Add customer button
        ctk.CTkButton(
            inner, text="➕ إضافة عميل", height=36, corner_radius=8,
            font=("Segoe UI", 13, "bold"), fg_color=PRIMARY, hover_color="#1557b0",
            command=self._add_customer
        ).pack(side="left")

        # ── Cards Grid ──
        self.cards_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_grid.pack(fill="both", expand=True)
        self.cards_grid.grid_columnconfigure((0, 1, 2), weight=1)

        # Empty label
        self.empty_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 14),
            text_color=TEXT_SEC
        )

    def _clear_grid(self):
        for widget in self.cards_grid.winfo_children():
            widget.destroy()
        self.empty_label.pack_forget()

    def _render_cards(self, customers):
        self._clear_grid()

        if not customers:
            self.empty_label.configure(text="لا يوجد عملاء مطابقين للبحث")
            self.empty_label.pack(pady=40)
            return

        for idx, customer in enumerate(customers):
            row = idx // 3
            col = idx % 3

            card = CustomerCard(
                self.cards_grid, customer,
                on_edit=self._edit_customer,
                on_delete=self._delete_customer,
                on_charge=self._charge_customer,
            )
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

    def _apply_filter(self):
        """Filter customers by search text against already-loaded list"""
        search = self.search_entry.get().strip().lower()
        filtered = []
        for c in self.customers_list:
            if search:
                if search not in c.name.lower() and search not in c.phone.lower():
                    continue
            filtered.append(c)
        self._render_cards(filtered)

    # ── Add Customer ──
    def _add_customer(self):
        dialog = CustomerDialog(self.winfo_toplevel())
        self.wait_window(dialog)

        if dialog.result:
            db = SessionLocal()
            try:
                create_customer(db, **dialog.result)
                self.refresh()
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                     parent=self.winfo_toplevel())
            finally:
                db.close()

    # ── Edit Customer ──
    def _edit_customer(self, customer):
        dialog = CustomerDialog(self.winfo_toplevel(), customer=customer)
        self.wait_window(dialog)

        if dialog.result:
            db = SessionLocal()
            try:
                update_customer(db, customer.id, **dialog.result)
                self.refresh()
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                     parent=self.winfo_toplevel())
            finally:
                db.close()

    # ── Delete Customer ──
    def _delete_customer(self, customer):
        if not messagebox.askyesno(
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف العميل \"{customer.name}\"؟\n"
            f"سيتم تعطيل الحساب وليس حذفه نهائياً.",
            parent=self.winfo_toplevel()
        ):
            return

        db = SessionLocal()
        try:
            if delete_customer(db, customer.id):
                self.refresh()
            else:
                messagebox.showerror("خطأ", "فشل في حذف العميل",
                                     parent=self.winfo_toplevel())
        finally:
            db.close()

    # ── Charge Balance ──
    def _charge_customer(self, customer):
        dialog = ChargeDialog(self.winfo_toplevel(), customer)
        self.wait_window(dialog)

        if dialog.result:
            db = SessionLocal()
            try:
                charge_customer_balance(db, customer.id, dialog.result["amount"])
                self.refresh()
                messagebox.showinfo(
                    "تم بنجاح",
                    f"تم شحن {fc(dialog.result['amount'])} لحساب {customer.name}",
                    parent=self.winfo_toplevel()
                )
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                     parent=self.winfo_toplevel())
            finally:
                db.close()

    # ── Refresh ──
    def refresh(self):
        db = SessionLocal()
        try:
            self.customers_list = get_customers(db, active_only=True)
            self.count_label.configure(text=f"إجمالي: {len(self.customers_list)} عميل")
            self._apply_filter()
        finally:
            db.close()