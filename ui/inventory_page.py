from main import *
from database.db import SessionLocal
from services.services import (
    add_inventory_item, get_inventory, update_inventory_quantity, delete_inventory_item
)
from tkinter import messagebox


CATEGORIES = [
    "كنترولر", "هيدفون", "كابل", "سناكس", "مشروبات", "إكسسوارات", "أخرى"
]

CATEGORY_MAP = {
    "الكل": None,
    "كنترولر": "كنترولر",
    "هيدفون": "هيدفون",
    "كابل": "كابل",
    "سناكس": "سناكس",
    "مشروبات": "مشروبات",
    "إكسسوارات": "إكسسوارات",
    "أخرى": "أخرى",
}


# ─── Dialog: Add Item ────────────────────────────────────────
class AddItemDialog(ctk.CTkToplevel):
    """نافذة إضافة صنف جديد للمخزون"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("إضافة صنف جديد")
        self.geometry("440x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result = None

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 440) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 480) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 20, "pady": 6}

        ctk.CTkLabel(
            self, text="📦 إضافة صنف جديد",
            font=("Segoe UI", 18, "bold"), text_color=TEXT
        ).pack(pady=(20, 10))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=5)

        # Name
        ctk.CTkLabel(
            form, text="اسم الصنف:", font=("Segoe UI", 13),
            text_color=TEXT, anchor="e"
        ).grid(row=0, column=0, sticky="e", **pad)
        self.name_entry = ctk.CTkEntry(
            form, width=260, height=36,
            font=("Segoe UI", 12), placeholder_text="مثال: كنترولر PS5"
        )
        self.name_entry.grid(row=0, column=1, sticky="w", **pad)

        # Category
        ctk.CTkLabel(
            form, text="التصنيف:", font=("Segoe UI", 13),
            text_color=TEXT, anchor="e"
        ).grid(row=1, column=0, sticky="e", **pad)
        self.category_var = ctk.StringVar(value=CATEGORIES[0])
        self.category_combo = ctk.CTkComboBox(
            form, values=CATEGORIES, variable=self.category_var,
            width=260, height=36, font=("Segoe UI", 12)
        )
        self.category_combo.grid(row=1, column=1, sticky="w", **pad)

        # Quantity
        ctk.CTkLabel(
            form, text="الكمية:", font=("Segoe UI", 13),
            text_color=TEXT, anchor="e"
        ).grid(row=2, column=0, sticky="e", **pad)
        self.qty_entry = ctk.CTkEntry(
            form, width=260, height=36,
            font=("Segoe UI", 12), placeholder_text="0"
        )
        self.qty_entry.grid(row=2, column=1, sticky="w", **pad)

        # Min quantity
        ctk.CTkLabel(
            form, text="الحد الأدنى:", font=("Segoe UI", 13),
            text_color=TEXT, anchor="e"
        ).grid(row=3, column=0, sticky="e", **pad)
        self.min_qty_entry = ctk.CTkEntry(
            form, width=260, height=36,
            font=("Segoe UI", 12), placeholder_text="5"
        )
        self.min_qty_entry.grid(row=3, column=1, sticky="w", **pad)

        # Unit price
        ctk.CTkLabel(
            form, text="سعر الوحدة (ج.م):", font=("Segoe UI", 13),
            text_color=TEXT, anchor="e"
        ).grid(row=4, column=0, sticky="e", **pad)
        self.price_entry = ctk.CTkEntry(
            form, width=260, height=36,
            font=("Segoe UI", 12), placeholder_text="0.00"
        )
        self.price_entry.grid(row=4, column=1, sticky="w", **pad)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(10, 20))

        ctk.CTkButton(
            btn_frame, text="إلغاء", width=120, height=38,
            font=("Segoe UI", 13), fg_color=SECONDARY, hover_color=SECONDARY_HOVER,
            command=self._cancel
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            btn_frame, text="💾 إضافة", width=120, height=38,
            font=("Segoe UI", 13, "bold"), fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            command=self._save
        ).pack(side="right", padx=8)

    def _cancel(self):
        self.result = None
        self.destroy()

    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("تحذير", "يرجى إدخال اسم الصنف", parent=self)
            return

        try:
            quantity = int(self.qty_entry.get().strip() or "0")
        except ValueError:
            messagebox.showwarning("تحذير", "يرجى إدخال رقم صحيح للكمية", parent=self)
            return

        try:
            min_quantity = int(self.min_qty_entry.get().strip() or "5")
        except ValueError:
            messagebox.showwarning("تحذير", "يرجى إدخال رقم صحيح للحد الأدنى", parent=self)
            return

        try:
            unit_price = float(self.price_entry.get().strip() or "0")
        except ValueError:
            messagebox.showwarning("تحذير", "يرجى إدخال رقم صحيح لسعر الوحدة", parent=self)
            return

        self.result = {
            "name": name,
            "category": self.category_var.get(),
            "quantity": quantity,
            "min_quantity": min_quantity,
            "unit_price": unit_price,
        }
        self.destroy()


# ─── Dialog: Update Quantity ──────────────────────────────────
class UpdateQtyDialog(ctk.CTkToplevel):
    """نافذة تحديث كمية صنف"""

    def __init__(self, parent, item):
        super().__init__(parent)
        self.title(f"تحديث الكمية — {item.name}")
        self.geometry("380x260")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.item = item
        self.result = None

        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 380) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 260) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="📝 تحديث الكمية",
            font=("Segoe UI", 18, "bold"), text_color=TEXT
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            self, text=f"📦 {self.item.name}  (الكمية الحالية: {self.item.quantity})",
            font=("Segoe UI", 13), text_color=TEXT_SEC
        ).pack(pady=(0, 10))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=5)

        ctk.CTkLabel(
            form, text="الكمية الجديدة:",
            font=("Segoe UI", 13), text_color=TEXT, anchor="e"
        ).pack(anchor="e", pady=(10, 4))

        self.qty_entry = ctk.CTkEntry(
            form, width=300, height=42,
            font=("Segoe UI", 14), placeholder_text="أدخل الكمية الجديدة"
        )
        self.qty_entry.pack(anchor="e", pady=(0, 10))
        self.qty_entry.insert(0, str(self.item.quantity))
        self.qty_entry.focus_set()
        self.qty_entry.select_range(0, "end")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(5, 20))

        ctk.CTkButton(
            btn_frame, text="إلغاء", width=120, height=38,
            font=("Segoe UI", 13), fg_color=SECONDARY, hover_color=SECONDARY_HOVER,
            command=self._cancel
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            btn_frame, text="💾 تحديث", width=120, height=38,
            font=("Segoe UI", 13, "bold"), fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            command=self._save
        ).pack(side="right", padx=8)

    def _cancel(self):
        self.result = None
        self.destroy()

    def _save(self):
        try:
            new_qty = int(self.qty_entry.get().strip())
        except ValueError:
            messagebox.showwarning("تحذير", "يرجى إدخال رقم صحيح", parent=self)
            return

        if new_qty < 0:
            messagebox.showwarning("تحذير", "الكمية لا يمكن أن تكون سالبة", parent=self)
            return

        self.result = {"new_quantity": new_qty}
        self.destroy()


# ─── Inventory Item Card ─────────────────────────────────────
class InventoryItemCard(ctk.CTkFrame):
    """بطاقة صنف مخزون واحد"""

    def __init__(self, master, item, is_low=False, on_edit=None, on_delete=None):
        super().__init__(master, fg_color=CARD_BG, corner_radius=12)
        if is_low:
            self.configure(border_width=2, border_color=DANGER)
        self.item = item
        self.is_low = is_low
        self.on_edit = on_edit
        self.on_delete = on_delete
        self._build()

    def _build(self):
        it = self.item

        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(14, 4))

        ctk.CTkLabel(
            header, text=f"📦 {it.name}",
            font=("Segoe UI", 15, "bold"), text_color=TEXT, anchor="e"
        ).pack(side="right", fill="x", expand=True)

        # Action buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="left")

        ctk.CTkButton(
            btn_frame, text="✏️", width=30, height=30, corner_radius=8,
            font=("", 13), fg_color="transparent", hover_color="#e0e7ff",
            command=lambda: self.on_edit(it) if self.on_edit else None
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_frame, text="🗑️", width=30, height=30, corner_radius=8,
            font=("", 13), fg_color="transparent", hover_color=DELETE_HOVER,
            command=lambda: self.on_delete(it) if self.on_delete else None
        ).pack(side="left", padx=2)

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=DIVIDER).pack(fill="x", padx=14, pady=4)

        # Category
        ctk.CTkLabel(
            self, text=f"📂 {it.category}",
            font=("Segoe UI", 12), text_color=TEXT_SEC, anchor="e"
        ).pack(fill="x", padx=14, pady=2)

        # Bottom stats: quantity/min + unit price
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.pack(fill="x", padx=14, pady=(6, 14))

        # Quantity label with color coding
        qty_color = DANGER if self.is_low else SUCCESS
        qty_text = f"📊 الكمية: {it.quantity} / {it.min_quantity}"

        if self.is_low:
            qty_text = f"⚠️ ناقص! {it.quantity} / {it.min_quantity}"

        ctk.CTkLabel(
            stats, text=qty_text,
            font=("Segoe UI", 13, "bold"), text_color=qty_color, anchor="e"
        ).pack(side="right", fill="x", expand=True)

        ctk.CTkLabel(
            stats, text=f"💰 {fc(it.unit_price)}",
            font=("Segoe UI", 13, "bold"), text_color="#2563eb", anchor="w"
        ).pack(side="left")


# ─── Inventory Page ──────────────────────────────────────────
class InventoryPage(BasePage):
    """صفحة إدارة المخزون"""

    def __init__(self, master, app):
        super().__init__(master, app, title="المخزون")
        self.inventory_list = []
        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            header, text="📦 إدارة المخزون",
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

        # Filter combobox
        ctk.CTkLabel(
            inner, text="📂 التصنيف:",
            font=("Segoe UI", 13, "bold"), text_color=TEXT, anchor="e"
        ).pack(side="right", padx=(0, 8))

        self.filter_var = ctk.StringVar(value="الكل")
        self.filter_combo = ctk.CTkComboBox(
            inner, values=list(CATEGORY_MAP.keys()),
            variable=self.filter_var,
            width=160, height=38, font=("Segoe UI", 12),
            command=lambda _: self._apply_filter()
        )
        self.filter_combo.pack(side="right", padx=(0, 16))

        # Add item button
        ctk.CTkButton(
            inner, text="➕ إضافة صنف", height=38, corner_radius=8,
            font=("Segoe UI", 13, "bold"), fg_color=SUCCESS, hover_color=SUCCESS_HOVER,
            command=self._add_item
        ).pack(side="left")

        # ── Low stock section ──
        self.low_stock_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.low_stock_grid = ctk.CTkScrollableFrame(self.low_stock_frame, fg_color="transparent")

        self.low_stock_header = ctk.CTkFrame(self.low_stock_frame, fg_color="transparent")
        self.low_stock_title = ctk.CTkLabel(
            self.low_stock_header, text="",
            font=("Segoe UI", 16, "bold"), text_color=DANGER, anchor="e"
        )
        self.low_stock_title.pack(side="right")

        self.low_stock_count = ctk.CTkLabel(
            self.low_stock_header, text="",
            font=("Segoe UI", 13), text_color=TEXT_SEC, anchor="e"
        )
        self.low_stock_count.pack(side="right", padx=12)

        # ── Normal items section ──
        self.normal_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.normal_grid = ctk.CTkScrollableFrame(self.normal_frame, fg_color="transparent")

        self.normal_header = ctk.CTkFrame(self.normal_frame, fg_color="transparent")
        self.normal_title = ctk.CTkLabel(
            self.normal_header, text="",
            font=("Segoe UI", 16, "bold"), text_color=SUCCESS, anchor="e"
        )
        self.normal_title.pack(side="right")

        self.normal_count = ctk.CTkLabel(
            self.normal_header, text="",
            font=("Segoe UI", 13), text_color=TEXT_SEC, anchor="e"
        )
        self.normal_count.pack(side="right", padx=12)

        # Empty label
        self.empty_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 14), text_color=TEXT_SEC
        )

    def _clear_sections(self):
        for widget in self.low_stock_frame.winfo_children():
            widget.destroy()
        for widget in self.normal_frame.winfo_children():
            widget.destroy()
        self.low_stock_frame.pack_forget()
        self.normal_frame.pack_forget()
        self.empty_label.pack_forget()

    def _rebuild_section_frames(self):
        """إعادة بناء الإطارات الداخلية بعد المسح"""
        # Low stock section
        self.low_stock_header = ctk.CTkFrame(self.low_stock_frame, fg_color="transparent")
        self.low_stock_title = ctk.CTkLabel(
            self.low_stock_header, text="",
            font=("Segoe UI", 16, "bold"), text_color=DANGER, anchor="e"
        )
        self.low_stock_title.pack(side="right")

        self.low_stock_count = ctk.CTkLabel(
            self.low_stock_header, text="",
            font=("Segoe UI", 13), text_color=TEXT_SEC, anchor="e"
        )
        self.low_stock_count.pack(side="right", padx=12)

        self.low_stock_grid = ctk.CTkScrollableFrame(self.low_stock_frame, fg_color="transparent")
        self.low_stock_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Normal section
        self.normal_header = ctk.CTkFrame(self.normal_frame, fg_color="transparent")
        self.normal_title = ctk.CTkLabel(
            self.normal_header, text="",
            font=("Segoe UI", 16, "bold"), text_color=SUCCESS, anchor="e"
        )
        self.normal_title.pack(side="right")

        self.normal_count = ctk.CTkLabel(
            self.normal_header, text="",
            font=("Segoe UI", 13), text_color=TEXT_SEC, anchor="e"
        )
        self.normal_count.pack(side="right", padx=12)

        self.normal_grid = ctk.CTkScrollableFrame(self.normal_frame, fg_color="transparent")
        self.normal_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

    def _render_items(self, items):
        self._clear_sections()
        self._rebuild_section_frames()

        if not items:
            self.empty_label.configure(text="لا توجد أصناف في المخزون")
            self.empty_label.pack(pady=40)
            return

        low_items = [it for it in items if it.quantity <= it.min_quantity]
        normal_items = [it for it in items if it.quantity > it.min_quantity]

        # ── Low stock section ──
        if low_items:
            self.low_stock_title.configure(text="⚠️ أصناف ناقصة")
            self.low_stock_count.configure(text=f"({len(low_items)} صنف)")

            self.low_stock_header.pack(fill="x", pady=(0, 8))
            self.low_stock_grid.pack(fill="x")

            for idx, it in enumerate(low_items):
                row = idx // 4
                col = idx % 4
                card = InventoryItemCard(
                    self.low_stock_grid, it, is_low=True,
                    on_edit=self._edit_quantity,
                    on_delete=self._delete_item,
                )
                card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        else:
            self.low_stock_frame.pack_forget()

        # ── Normal items section ──
        if normal_items:
            self.normal_title.configure(text="✅ أصناف متوفرة")
            self.normal_count.configure(text=f"({len(normal_items)} صنف)")

            self.normal_header.pack(fill="x", pady=(16 if low_items else 0, 8))
            self.normal_grid.pack(fill="x")

            for idx, it in enumerate(normal_items):
                row = idx // 4
                col = idx % 4
                card = InventoryItemCard(
                    self.normal_grid, it, is_low=False,
                    on_edit=self._edit_quantity,
                    on_delete=self._delete_item,
                )
                card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        else:
            self.normal_frame.pack_forget()

        # Pack sections
        if low_items:
            self.low_stock_frame.pack(fill="x", pady=(0, 5))
        if normal_items:
            self.normal_frame.pack(fill="x", pady=(5, 0))

    def _apply_filter(self):
        """تصفية الأصناف حسب التصنيف المختار من القائمة المحملة"""
        selected = self.filter_var.get()
        category = CATEGORY_MAP.get(selected)
        filtered = []
        for it in self.inventory_list:
            if category is not None and it.category != category:
                continue
            filtered.append(it)
        self._render_items(filtered)

    # ── Add Item ──
    def _add_item(self):
        dialog = AddItemDialog(self.winfo_toplevel())
        self.wait_window(dialog)

        if dialog.result:
            db = SessionLocal()
            try:
                add_inventory_item(db, **dialog.result)
                self.refresh()
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                     parent=self.winfo_toplevel())
            finally:
                db.close()

    # ── Edit Quantity ──
    def _edit_quantity(self, item):
        dialog = UpdateQtyDialog(self.winfo_toplevel(), item)
        self.wait_window(dialog)

        if dialog.result:
            db = SessionLocal()
            try:
                update_inventory_quantity(db, item.id, dialog.result["new_quantity"])
                self.refresh()
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                     parent=self.winfo_toplevel())
            finally:
                db.close()

    # ── Delete Item ──
    def _delete_item(self, item):
        if not messagebox.askyesno(
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف الصنف \"{item.name}\"؟\n"
            f"لا يمكن التراجع عن هذا الإجراء.",
            parent=self.winfo_toplevel()
        ):
            return

        db = SessionLocal()
        try:
            if delete_inventory_item(db, item.id):
                self.refresh()
            else:
                messagebox.showerror("خطأ", "فشل في حذف الصنف",
                                     parent=self.winfo_toplevel())
        finally:
            db.close()

    # ── Refresh ──
    def refresh(self):
        db = SessionLocal()
        try:
            self.inventory_list = get_inventory(db)
            self.count_label.configure(
                text=f"إجمالي: {len(self.inventory_list)} صنف"
            )
            self._apply_filter()
        finally:
            db.close()