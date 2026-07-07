from main import *
from services.services import (
    create_station, get_stations, get_station_by_id,
    update_station, delete_station, get_station_stats
)
from tkinter import messagebox


class StationDialog(ctk.CTkToplevel):
    """نافذة إضافة / تعديل محطة"""

    def __init__(self, parent, station=None):
        super().__init__(parent)
        self.title("تعديل محطة" if station else "إضافة محطة جديدة")
        self.geometry("420x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.station = station
        self.result = None

        # تحديد المركز
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 420) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 480) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()
        if station:
            self._fill_data(station)

    def _build_ui(self):
        pad = {"padx": 20, "pady": 6}

        # عنوان
        title = "تعديل محطة" if self.station else "إضافة محطة جديدة"
        ctk.CTkLabel(
            self, text=f"🎮 {title}", font=("Segoe UI", 18, "bold"),
            text_color=TEXT
        ).pack(pady=(20, 10))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=5)

        # اسم المحطة
        ctk.CTkLabel(form, text="اسم المحطة:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=0, column=0, sticky="e", **pad)
        self.name_entry = ctk.CTkEntry(form, width=260, height=36,
                                        font=("Segoe UI", 12), placeholder_text="مثال: محطة ١")
        self.name_entry.grid(row=0, column=1, sticky="w", **pad)

        # نوع الجهاز
        ctk.CTkLabel(form, text="نوع الجهاز:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=1, column=0, sticky="e", **pad)
        self.console_var = ctk.StringVar(value="PS5")
        self.console_combo = ctk.CTkComboBox(
            form, values=["PS4", "PS5"], variable=self.console_var,
            width=260, height=36, font=("Segoe UI", 12)
        )
        self.console_combo.grid(row=1, column=1, sticky="w", **pad)

        # سعر الساعة
        ctk.CTkLabel(form, text="سعر الساعة (ج.م):", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=2, column=0, sticky="e", **pad)
        self.rate_entry = ctk.CTkEntry(form, width=260, height=36,
                                        font=("Segoe UI", 12), placeholder_text="30")
        self.rate_entry.grid(row=2, column=1, sticky="w", **pad)

        # عدد المقبضات
        ctk.CTkLabel(form, text="عدد المقبضات:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=3, column=0, sticky="e", **pad)
        self.controller_entry = ctk.CTkEntry(form, width=260, height=36,
                                              font=("Segoe UI", 12), placeholder_text="2")
        self.controller_entry.grid(row=3, column=1, sticky="w", **pad)

        # نظارة VR
        self.vr_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            form, text="نظارة VR متوفرة", variable=self.vr_var,
            font=("Segoe UI", 13), text_color=TEXT, checkbox_width=20,
            checkbox_height=20
        ).grid(row=4, column=0, columnspan=2, sticky="w", padx=20, pady=8)

        # داسة / مقود
        self.wheel_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            form, text="داسة / مقود متوفرة", variable=self.wheel_var,
            font=("Segoe UI", 13), text_color=TEXT, checkbox_width=20,
            checkbox_height=20
        ).grid(row=5, column=0, columnspan=2, sticky="w", padx=20, pady=4)

        # أزرار الحفظ والإلغاء
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(5, 20))

        ctk.CTkButton(
            btn_frame, text="إلغاء", width=120, height=38,
            font=("Segoe UI", 13), fg_color=SECONDARY, hover_color=SECONDARY_HOVER,
            command=self._cancel
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            btn_frame, text="💾 حفظ", width=120, height=38,
            font=("Segoe UI", 13), fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            command=self._save
        ).pack(side="right", padx=8)

    def _fill_data(self, station):
        self.name_entry.insert(0, station.name)
        self.console_var.set(station.console_type)
        self.rate_entry.insert(0, str(station.hourly_rate))
        self.controller_entry.insert(0, str(station.controller_count))
        self.vr_var.set(station.has_vr)
        self.wheel_var.set(station.has_wheel)

    def _cancel(self):
        self.result = None
        self.destroy()

    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("تحذير", "يرجى إدخال اسم المحطة", parent=self)
            return

        try:
            rate = float(self.rate_entry.get()) if self.rate_entry.get().strip() else None
        except ValueError:
            messagebox.showwarning("تحذير", "يرجى إدخال رقم صحيح لسعر الساعة", parent=self)
            return

        try:
            controllers = int(self.controller_entry.get()) if self.controller_entry.get().strip() else 2
        except ValueError:
            messagebox.showwarning("تحذير", "يرجى إدخال رقم صحيح لعدد المقبضات", parent=self)
            return

        self.result = {
            "name": name,
            "console_type": self.console_var.get(),
            "hourly_rate": rate,
            "controller_count": controllers,
            "has_vr": self.vr_var.get(),
            "has_wheel": self.wheel_var.get(),
        }
        self.destroy()


class StationCard(ctk.CTkFrame):
    """بطاقة محطة واحدة"""

    def __init__(self, master, station, on_edit=None, on_delete=None, on_context=None):
        super().__init__(master, fg_color=CARD_BG, corner_radius=12)
        self.station = station
        self.on_edit = on_edit
        self.on_delete = on_delete

        self._build(station)

        # قائمة النقر الأيمن
        if on_context:
            self.bind("<Button-3>", lambda e: on_context(e, station))
            for child in self.winfo_children():
                child.bind("<Button-3>", lambda e: on_context(e, station))

    def _build(self, s):
        # رأس البطاقة: اسم المحطة + الأزرار
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(14, 4))

        ctk.CTkLabel(
            header, text=f"🎮 {s.name}", font=("Segoe UI", 15, "bold"),
            text_color=TEXT, anchor="e"
        ).pack(side="right", fill="x", expand=True)

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="left")

        edit_btn = ctk.CTkButton(
            btn_frame, text="✏️", width=30, height=30, corner_radius=8,
            font=("", 13), fg_color="transparent", hover_color="#e0e7ff",
            command=lambda: self.on_edit(s) if self.on_edit else None
        )
        edit_btn.pack(side="left", padx=2)

        del_btn = ctk.CTkButton(
            btn_frame, text="🗑️", width=30, height=30, corner_radius=8,
            font=("", 13), fg_color="transparent", hover_color=DELETE_HOVER,
            command=lambda: self.on_delete(s) if self.on_delete else None
        )
        del_btn.pack(side="left", padx=2)

        # فاصل
        ctk.CTkFrame(self, height=1, fg_color=DIVIDER).pack(fill="x", padx=14, pady=4)

        # نوع الجهاز
        console_icon = "🟦" if s.console_type == "PS5" else "🟪"
        ctk.CTkLabel(
            self, text=f"{console_icon}  {s.console_type}",
            font=("Segoe UI", 12), text_color=TEXT_SEC, anchor="e"
        ).pack(fill="x", padx=14, pady=2)

        # الحالة
        status_color = STATUS_COLORS.get(s.status, TEXT_SEC)
        status_text = STATUS_LABELS.get(s.status, s.status)
        ctk.CTkLabel(
            self, text=f"حالة: {status_text}",
            font=("Segoe UI", 12, "bold"), text_color=status_color, anchor="e"
        ).pack(fill="x", padx=14, pady=2)

        # سعر الساعة
        ctk.CTkLabel(
            self, text=f"💰 {fc(s.hourly_rate)} / ساعة",
            font=("Segoe UI", 12), text_color=TEXT_SEC, anchor="e"
        ).pack(fill="x", padx=14, pady=2)

        # عدد المقبضات
        ctk.CTkLabel(
            self, text=f"🎮 مقبضات: {s.controller_count}",
            font=("Segoe UI", 12), text_color=TEXT_SEC, anchor="e"
        ).pack(fill="x", padx=14, pady=(2, 14))


class StationsPage(BasePage):
    """صفحة إدارة المحطات"""

    def __init__(self, master, app):
        super().__init__(master, app, title="المحطات")
        self._build_ui()

    def _build_ui(self):
        # ── عنوان الصفحة ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            header, text="🎮 إدارة المحطات", font=("Segoe UI", 22, "bold"),
            text_color=TEXT, anchor="e"
        ).pack(side="right")

        self.count_label = ctk.CTkLabel(
            header, text="", font=("Segoe UI", 13),
            text_color=TEXT_SEC, anchor="e"
        )
        self.count_label.pack(side="left", padx=10)

        # ── شريط البحث والفلاتر ──
        toolbar = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        toolbar.pack(fill="x", pady=(0, 15))

        inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        # حقل البحث
        ctk.CTkLabel(inner, text="🔍", font=("", 16), anchor="e").pack(side="right", padx=(0, 6))
        self.search_entry = ctk.CTkEntry(
            inner, width=220, height=36, font=("Segoe UI", 12),
            placeholder_text="بحث بالاسم..."
        )
        self.search_entry.pack(side="right", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self._apply_filter())

        # فلتر الحالة
        ctk.CTkLabel(inner, text="الفلاتر:", font=("Segoe UI", 12),
                      text_color=TEXT_SEC, anchor="e").pack(side="right", padx=(0, 6))

        self.filter_var = ctk.StringVar(value="all")
        filter_map = {"all": "الكل", "available": "فارغة", "occupied": "مشغولة", "maintenance": "صيانة"}
        self.filter_combo = ctk.CTkComboBox(
            inner, values=list(filter_map.values()), variable=self.filter_var,
            width=140, height=36, font=("Segoe UI", 12),
            command=lambda v: self._apply_filter()
        )
        self.filter_combo.set("الكل")
        self.filter_combo.pack(side="right", padx=(0, 10))

        # زر إضافة محطة
        ctk.CTkButton(
            inner, text="➕ إضافة محطة", height=36, corner_radius=8,
            font=("Segoe UI", 13, "bold"), fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            command=self._add_station
        ).pack(side="left")

        # ── شبكة البطاقات ──
        self.cards_grid = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.cards_grid.pack(fill="both", expand=True)
        self.cards_grid.grid_columnconfigure((0, 1, 2), weight=1)

        # ── رسالة فارغة ──
        self.empty_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 14),
            text_color=TEXT_SEC
        )

        self.stations = []

    def _get_filter_key(self):
        """تحويل قيمة الفلتر إلى مفتاح إنجليزي"""
        mapping = {"الكل": "all", "فارغة": "available", "مشغولة": "occupied", "صيانة": "maintenance"}
        return mapping.get(self.filter_var.get(), "all")

    def _apply_filter(self):
        """تطبيق البحث والفلتر على المحطات المعروضة"""
        search = self.search_entry.get().strip().lower()
        filter_key = self._get_filter_key()

        filtered = []
        for s in self.stations:
            if search and search not in s.name.lower():
                continue
            if filter_key != "all" and s.status != filter_key:
                continue
            filtered.append(s)

        self._render_cards(filtered)

    def _clear_grid(self):
        for widget in self.cards_grid.winfo_children():
            widget.destroy()
        self.empty_label.pack_forget()

    def _render_cards(self, stations):
        self._clear_grid()

        if not stations:
            self.empty_label.configure(text="لا توجد محطات مطابقة للبحث")
            self.empty_label.pack(pady=40)
            return

        for idx, station in enumerate(stations):
            row = idx // 3
            col = idx % 3

            card = StationCard(
                self.cards_grid, station,
                on_edit=self._edit_station,
                on_delete=self._delete_station,
                on_context=self._show_context_menu
            )
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

    def _show_context_menu(self, event, station):
        """قائمة النقر الأيمن"""
        menu = tk.Menu(self, tearoff=0, font=("Segoe UI", 11))
        menu.add_command(label=f"🎮  {station.name}", state="disabled")
        menu.add_separator()
        menu.add_command(label="✏️  تعديل", command=lambda: self._edit_station(station))
        menu.add_command(
            label="🔄  تغيير الحالة", command=lambda: self._cycle_status(station)
        )
        menu.add_separator()
        menu.add_command(
            label="🗑️  حذف", command=lambda: self._delete_station(station)
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _cycle_status(self, station):
        """تبديل حالة المحطة"""
        status_cycle = ["available", "occupied", "maintenance"]
        try:
            idx = status_cycle.index(station.status)
            new_status = status_cycle[(idx + 1) % len(status_cycle)]
        except ValueError:
            new_status = "available"

        db = SessionLocal()
        try:
            update_station(db, station.id, status=new_status)
            self.refresh()
        finally:
            db.close()

    def _add_station(self):
        """فتح نافذة إضافة محطة"""
        dialog = StationDialog(self.winfo_toplevel())
        self.wait_window(dialog)

        if dialog.result:
            db = SessionLocal()
            try:
                create_station(db, **dialog.result)
                self.refresh()
            finally:
                db.close()

    def _edit_station(self, station):
        """فتح نافذة تعديل محطة"""
        dialog = StationDialog(self.winfo_toplevel(), station=station)
        self.wait_window(dialog)

        if dialog.result:
            db = SessionLocal()
            try:
                update_station(db, station.id, **dialog.result)
                self.refresh()
            finally:
                db.close()

    def _delete_station(self, station):
        """حذف محطة مع تأكيد"""
        if not messagebox.askyesno(
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف المحطة \"{station.name}\"؟",
            parent=self.winfo_toplevel()
        ):
            return

        db = SessionLocal()
        try:
            if delete_station(db, station.id):
                self.refresh()
            else:
                messagebox.showerror("خطأ", "فشل في حذف المحطة", parent=self.winfo_toplevel())
        finally:
            db.close()

    def refresh(self):
        """تحديث قائمة المحطات"""
        db = SessionLocal()
        try:
            self.stations = get_stations(db)
            self.count_label.configure(text=f"إجمالي: {len(self.stations)} محطة")
            self._apply_filter()
        finally:
            db.close()