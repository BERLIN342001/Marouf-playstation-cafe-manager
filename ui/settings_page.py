from main import *
from database.db import SessionLocal, DB_PATH, init_db, engine
from services.services import (
    get_setting, set_setting, get_hourly_rate,
    create_package, get_packages, delete_package,
    create_game, get_games, delete_game,
    get_stations, update_station
)
from tkinter import messagebox
import os


# ─── Settings Page ──────────────────────────────────────────
class SettingsPage(BasePage):
    """صفحة الإعدادات"""

    TABS = ["عام", "الأسعار", "الباقات", "الألعاب", "النظام"]
    PLATFORMS = ["PS5", "PS4", "Xbox Series X", "Xbox One", "PC", "Nintendo Switch"]

    def __init__(self, master, app):
        super().__init__(master, app, title="الإعدادات")
        self._build_ui()
        self.seg.set("عام")
        self._show_tab("عام")

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header, text="⚙️ الإعدادات",
            font=("Segoe UI", 22, "bold"), text_color=TEXT, anchor="e"
        ).pack(side="right")

        # Segmented button
        seg_frame = ctk.CTkFrame(self, fg_color="transparent")
        seg_frame.pack(fill="x", pady=(0, 15))

        self.seg = ctk.CTkSegmentedButton(
            seg_frame, values=self.TABS, command=self._show_tab,
            font=("Segoe UI", 13), height=40, corner_radius=10,
            selected_color=PRIMARY, selected_hover_color="#1557b0"
        )
        self.seg.pack(fill="x")

        # Content frame
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True)

    # ── Tab Router ──
    def _show_tab(self, tab_name):
        for w in self.content.winfo_children():
            w.destroy()

        if tab_name == "عام":
            self._build_general_tab()
        elif tab_name == "الأسعار":
            self._build_pricing_tab()
        elif tab_name == "الباقات":
            self._build_packages_tab()
        elif tab_name == "الألعاب":
            self._build_games_tab()
        elif tab_name == "النظام":
            self._build_system_tab()

    # ════════════════════════════════════════════════════════
    #  GENERAL TAB
    # ════════════════════════════════════════════════════════
    def _build_general_tab(self):
        card = ctk.CTkFrame(self.content, fg_color=CARD_BG, corner_radius=12)
        card.pack(fill="x", pady=5)

        ctk.CTkLabel(
            card, text="🏢 إعدادات عامة",
            font=("Segoe UI", 16, "bold"), text_color=TEXT, anchor="e"
        ).pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkFrame(card, height=1, fg_color="#e5e7eb").pack(fill="x", padx=20)

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=15)
        form.grid_columnconfigure(1, weight=1)

        pad = {"padx": 15, "pady": 8}

        # Cafe Name
        db = SessionLocal()
        try:
            cafe_name = get_setting(db, "cafe_name", "Marouf PlayStation Cafe")
            phone = get_setting(db, "phone", "")
            points_rate = get_setting(db, "points_rate", "10")
        finally:
            db.close()

        ctk.CTkLabel(form, text="اسم المقهى:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=0, column=0, sticky="e", **pad)
        self.gen_name_entry = ctk.CTkEntry(form, width=350, height=36, font=("Segoe UI", 12))
        self.gen_name_entry.grid(row=0, column=1, sticky="w", **pad)
        self.gen_name_entry.insert(0, cafe_name)

        ctk.CTkLabel(form, text="رقم الهاتف:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=1, column=0, sticky="e", **pad)
        self.gen_phone_entry = ctk.CTkEntry(form, width=350, height=36, font=("Segoe UI", 12))
        self.gen_phone_entry.grid(row=1, column=1, sticky="w", **pad)
        self.gen_phone_entry.insert(0, phone)

        ctk.CTkLabel(form, text="نقاط كل (ج.م):", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=2, column=0, sticky="e", **pad)
        self.gen_points_entry = ctk.CTkEntry(form, width=350, height=36, font=("Segoe UI", 12))
        self.gen_points_entry.grid(row=2, column=1, sticky="w", **pad)
        self.gen_points_entry.insert(0, points_rate)

        # Save button
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_frame, text="💾 حفظ الإعدادات العامة", height=38, corner_radius=8,
            font=("Segoe UI", 13, "bold"), fg_color=PRIMARY, hover_color="#1557b0",
            command=self._save_general
        ).pack(anchor="e", padx=15)

    def _save_general(self):
        db = SessionLocal()
        try:
            set_setting(db, "cafe_name", self.gen_name_entry.get().strip())
            set_setting(db, "phone", self.gen_phone_entry.get().strip())
            set_setting(db, "points_rate", self.gen_points_entry.get().strip())
            messagebox.showinfo("تم", "تم حفظ الإعدادات العامة بنجاح",
                                parent=self.winfo_toplevel())
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                 parent=self.winfo_toplevel())
        finally:
            db.close()

    # ════════════════════════════════════════════════════════
    #  PRICING TAB
    # ════════════════════════════════════════════════════════
    def _build_pricing_tab(self):
        card = ctk.CTkFrame(self.content, fg_color=CARD_BG, corner_radius=12)
        card.pack(fill="x", pady=5)

        ctk.CTkLabel(
            card, text="💰 إعدادات الأسعار",
            font=("Segoe UI", 16, "bold"), text_color=TEXT, anchor="e"
        ).pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkFrame(card, height=1, fg_color="#e5e7eb").pack(fill="x", padx=20)

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=15)
        form.grid_columnconfigure(1, weight=1)

        pad = {"padx": 15, "pady": 8}

        db = SessionLocal()
        try:
            normal_rate = get_hourly_rate(db)
            weekend_rate = get_setting(db, "weekend_rate", str(normal_rate))
            holiday_rate = get_setting(db, "holiday_rate", str(normal_rate))
        finally:
            db.close()

        ctk.CTkLabel(form, text="السعر العادي (ج.م/ساعة):", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=0, column=0, sticky="e", **pad)
        self.price_normal = ctk.CTkEntry(form, width=350, height=36, font=("Segoe UI", 12))
        self.price_normal.grid(row=0, column=1, sticky="w", **pad)
        self.price_normal.insert(0, str(normal_rate))

        ctk.CTkLabel(form, text="سعر عطلة نهاية الأسبوع (ج.م/ساعة):", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=1, column=0, sticky="e", **pad)
        self.price_weekend = ctk.CTkEntry(form, width=350, height=36, font=("Segoe UI", 12))
        self.price_weekend.grid(row=1, column=1, sticky="w", **pad)
        self.price_weekend.insert(0, weekend_rate)

        ctk.CTkLabel(form, text="سعر الأعياد (ج.م/ساعة):", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=2, column=0, sticky="e", **pad)
        self.price_holiday = ctk.CTkEntry(form, width=350, height=36, font=("Segoe UI", 12))
        self.price_holiday.grid(row=2, column=1, sticky="w", **pad)
        self.price_holiday.insert(0, holiday_rate)

        # Save button
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_frame, text="💾 حفظ الأسعار وتحديث المحطات", height=38, corner_radius=8,
            font=("Segoe UI", 13, "bold"), fg_color=PRIMARY, hover_color="#1557b0",
            command=self._save_pricing
        ).pack(anchor="e", padx=15)

    def _save_pricing(self):
        try:
            normal = float(self.price_normal.get().strip())
            weekend = float(self.price_weekend.get().strip())
            holiday = float(self.price_holiday.get().strip())
        except ValueError:
            messagebox.showwarning("تحذير", "يرجى إدخال أرقام صحيحة",
                                   parent=self.winfo_toplevel())
            return

        db = SessionLocal()
        try:
            set_setting(db, "hourly_rate", str(normal))
            set_setting(db, "weekend_rate", str(weekend))
            set_setting(db, "holiday_rate", str(holiday))

            # Update all stations with the new normal rate
            stations = get_stations(db)
            for s in stations:
                update_station(db, s.id, hourly_rate=normal)

            messagebox.showinfo(
                "تم", f"تم حفظ الأسعار وتحديث {len(stations)} محطة بنجاح",
                parent=self.winfo_toplevel()
            )
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                 parent=self.winfo_toplevel())
        finally:
            db.close()

    # ════════════════════════════════════════════════════════
    #  PACKAGES TAB
    # ════════════════════════════════════════════════════════
    def _build_packages_tab(self):
        # List card
        list_card = ctk.CTkFrame(self.content, fg_color=CARD_BG, corner_radius=12)
        list_card.pack(fill="both", expand=True, pady=(5, 5))

        header = ctk.CTkFrame(list_card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            header, text="📦 الباقات المتاحة",
            font=("Segoe UI", 16, "bold"), text_color=TEXT, anchor="e"
        ).pack(side="right", fill="x", expand=True)

        ctk.CTkFrame(list_card, height=1, fg_color="#e5e7eb").pack(fill="x", padx=20, pady=5)

        # Column headers
        col_hdr = ctk.CTkFrame(list_card, fg_color="transparent")
        col_hdr.pack(fill="x", padx=20, pady=(0, 5))

        for col, (txt, w, anchor) in enumerate([
            ("الاسم", 150, "center"), ("الساعات", 80, "center"),
            ("السعر", 100, "center"), ("الساعة", 100, "center"), ("", 80, "center")
        ]):
            ctk.CTkLabel(
                col_hdr, text=txt, font=("Segoe UI", 12, "bold"),
                text_color=TEXT, width=w, anchor=anchor
            ).pack(side="right", padx=6)

        # Packages list
        pkg_container = ctk.CTkFrame(list_card, fg_color="transparent")
        pkg_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        db = SessionLocal()
        try:
            packages = get_packages(db)
        finally:
            db.close()

        if not packages:
            ctk.CTkLabel(
                pkg_container, text="لا توجد باقات حالياً",
                font=("Segoe UI", 13), text_color=TEXT_SEC
            ).pack(pady=20)
        else:
            for p in packages:
                hourly = round(p.price / p.hours, 2) if p.hours > 0 else 0
                row = ctk.CTkFrame(pkg_container, fg_color="#f9fafb", corner_radius=8)
                row.pack(fill="x", pady=3)

                ctk.CTkLabel(row, text=p.name, font=("Segoe UI", 12),
                              text_color=TEXT, width=150, anchor="center").pack(side="right", padx=6, pady=8)
                ctk.CTkLabel(row, text=str(p.hours), font=("Segoe UI", 12),
                              text_color=TEXT, width=80, anchor="center").pack(side="right", padx=6, pady=8)
                ctk.CTkLabel(row, text=fc(p.price), font=("Segoe UI", 12, "bold"),
                              text_color=PRIMARY, width=100, anchor="center").pack(side="right", padx=6, pady=8)
                ctk.CTkLabel(row, text=fc(hourly), font=("Segoe UI", 11),
                              text_color=TEXT_SEC, width=100, anchor="center").pack(side="right", padx=6, pady=8)

                ctk.CTkButton(
                    row, text="🗑️", width=40, height=30, corner_radius=8,
                    font=("", 12), fg_color="transparent", hover_color="#fee2e2",
                    command=lambda pid=p.id: self._delete_package(pid)
                ).pack(side="left", padx=6, pady=8)

        # Add form card
        add_card = ctk.CTkFrame(self.content, fg_color=CARD_BG, corner_radius=12)
        add_card.pack(fill="x", pady=(5, 5))

        ctk.CTkLabel(
            add_card, text="➕ إضافة باقة جديدة",
            font=("Segoe UI", 15, "bold"), text_color=TEXT, anchor="e"
        ).pack(fill="x", padx=20, pady=(12, 8))

        form = ctk.CTkFrame(add_card, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(form, text="الاسم:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").pack(side="right", padx=(0, 6))
        self.pkg_name = ctk.CTkEntry(form, width=150, height=36, font=("Segoe UI", 12))
        self.pkg_name.pack(side="right", padx=(0, 15))

        ctk.CTkLabel(form, text="الساعات:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").pack(side="right", padx=(0, 6))
        self.pkg_hours = ctk.CTkEntry(form, width=100, height=36, font=("Segoe UI", 12))
        self.pkg_hours.pack(side="right", padx=(0, 15))

        ctk.CTkLabel(form, text="السعر (ج.م):", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").pack(side="right", padx=(0, 6))
        self.pkg_price = ctk.CTkEntry(form, width=100, height=36, font=("Segoe UI", 12))
        self.pkg_price.pack(side="right", padx=(0, 15))

        ctk.CTkButton(
            form, text="➕ إضافة", fg_color=SUCCESS, hover_color="#16a34a",
            width=100, height=36, font=("Segoe UI", 13, "bold"),
            command=self._add_package
        ).pack(side="left")

    def _add_package(self):
        name = self.pkg_name.get().strip()
        if not name:
            messagebox.showwarning("تحذير", "يرجى إدخال اسم الباقة",
                                   parent=self.winfo_toplevel())
            return
        try:
            hours = float(self.pkg_hours.get().strip())
            price = float(self.pkg_price.get().strip())
            if hours <= 0 or price <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("تحذير", "يرجى إدخال قيم صحيحة للساعات والسعر",
                                   parent=self.winfo_toplevel())
            return

        db = SessionLocal()
        try:
            create_package(db, name, hours, price)
            self._show_tab("الباقات")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                 parent=self.winfo_toplevel())
        finally:
            db.close()

    def _delete_package(self, package_id):
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذه الباقة؟",
                                    parent=self.winfo_toplevel()):
            return
        db = SessionLocal()
        try:
            delete_package(db, package_id)
            self._show_tab("الباقات")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                 parent=self.winfo_toplevel())
        finally:
            db.close()

    # ════════════════════════════════════════════════════════
    #  GAMES TAB
    # ════════════════════════════════════════════════════════
    def _build_games_tab(self):
        # List card
        list_card = ctk.CTkFrame(self.content, fg_color=CARD_BG, corner_radius=12)
        list_card.pack(fill="both", expand=True, pady=(5, 5))

        header = ctk.CTkFrame(list_card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            header, text="🎮 الألعاب المتاحة",
            font=("Segoe UI", 16, "bold"), text_color=TEXT, anchor="e"
        ).pack(side="right", fill="x", expand=True)

        ctk.CTkFrame(list_card, height=1, fg_color="#e5e7eb").pack(fill="x", padx=20, pady=5)

        # Column headers
        col_hdr = ctk.CTkFrame(list_card, fg_color="transparent")
        col_hdr.pack(fill="x", padx=20, pady=(0, 5))

        for col, (txt, w, anchor) in enumerate([
            ("اسم اللعبة", 200, "center"), ("المنصة", 140, "center"),
            ("النسخ", 80, "center"), ("", 80, "center")
        ]):
            ctk.CTkLabel(
                col_hdr, text=txt, font=("Segoe UI", 12, "bold"),
                text_color=TEXT, width=w, anchor=anchor
            ).pack(side="right", padx=6)

        # Games list
        games_container = ctk.CTkFrame(list_card, fg_color="transparent")
        games_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        db = SessionLocal()
        try:
            games = get_games(db)
        finally:
            db.close()

        if not games:
            ctk.CTkLabel(
                games_container, text="لا توجد ألعاب حالياً",
                font=("Segoe UI", 13), text_color=TEXT_SEC
            ).pack(pady=20)
        else:
            for g in games:
                row = ctk.CTkFrame(games_container, fg_color="#f9fafb", corner_radius=8)
                row.pack(fill="x", pady=3)

                ctk.CTkLabel(row, text=g.name, font=("Segoe UI", 12),
                              text_color=TEXT, width=200, anchor="center").pack(side="right", padx=6, pady=8)
                ctk.CTkLabel(row, text=g.platform, font=("Segoe UI", 12),
                              text_color=TEXT_SEC, width=140, anchor="center").pack(side="right", padx=6, pady=8)
                ctk.CTkLabel(row, text=str(g.total_copies), font=("Segoe UI", 12, "bold"),
                              text_color=PRIMARY, width=80, anchor="center").pack(side="right", padx=6, pady=8)

                ctk.CTkButton(
                    row, text="🗑️", width=40, height=30, corner_radius=8,
                    font=("", 12), fg_color="transparent", hover_color="#fee2e2",
                    command=lambda gid=g.id: self._delete_game(gid)
                ).pack(side="left", padx=6, pady=8)

        # Add form card
        add_card = ctk.CTkFrame(self.content, fg_color=CARD_BG, corner_radius=12)
        add_card.pack(fill="x", pady=(5, 5))

        ctk.CTkLabel(
            add_card, text="➕ إضافة لعبة جديدة",
            font=("Segoe UI", 15, "bold"), text_color=TEXT, anchor="e"
        ).pack(fill="x", padx=20, pady=(12, 8))

        form = ctk.CTkFrame(add_card, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(form, text="اسم اللعبة:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").pack(side="right", padx=(0, 6))
        self.game_name = ctk.CTkEntry(form, width=200, height=36, font=("Segoe UI", 12))
        self.game_name.pack(side="right", padx=(0, 15))

        ctk.CTkLabel(form, text="المنصة:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").pack(side="right", padx=(0, 6))
        self.game_platform = ctk.CTkComboBox(
            form, values=self.PLATFORMS, width=150, height=36, font=("Segoe UI", 12)
        )
        self.game_platform.pack(side="right", padx=(0, 15))

        ctk.CTkLabel(form, text="عدد النسخ:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").pack(side="right", padx=(0, 6))
        self.game_copies = ctk.CTkEntry(form, width=80, height=36, font=("Segoe UI", 12))
        self.game_copies.pack(side="right", padx=(0, 15))
        self.game_copies.insert(0, "1")

        ctk.CTkButton(
            form, text="➕ إضافة", fg_color=SUCCESS, hover_color="#16a34a",
            width=100, height=36, font=("Segoe UI", 13, "bold"),
            command=self._add_game
        ).pack(side="left")

    def _add_game(self):
        name = self.game_name.get().strip()
        if not name:
            messagebox.showwarning("تحذير", "يرجى إدخال اسم اللعبة",
                                   parent=self.winfo_toplevel())
            return

        platform = self.game_platform.get()
        try:
            copies = int(self.game_copies.get().strip())
            if copies <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("تحذير", "يرجى إدخال عدد نسخ صحيح",
                                   parent=self.winfo_toplevel())
            return

        db = SessionLocal()
        try:
            create_game(db, name=name, platform=platform, total_copies=copies)
            self._show_tab("الألعاب")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                 parent=self.winfo_toplevel())
        finally:
            db.close()

    def _delete_game(self, game_id):
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذه اللعبة؟",
                                    parent=self.winfo_toplevel()):
            return
        db = SessionLocal()
        try:
            delete_game(db, game_id)
            self._show_tab("الألعاب")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                 parent=self.winfo_toplevel())
        finally:
            db.close()

    # ════════════════════════════════════════════════════════
    #  SYSTEM TAB
    # ════════════════════════════════════════════════════════
    def _build_system_tab(self):
        # DB Info card
        info_card = ctk.CTkFrame(self.content, fg_color=CARD_BG, corner_radius=12)
        info_card.pack(fill="x", pady=5)

        ctk.CTkLabel(
            info_card, text="🗄️ معلومات قاعدة البيانات",
            font=("Segoe UI", 16, "bold"), text_color=TEXT, anchor="e"
        ).pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkFrame(info_card, height=1, fg_color="#e5e7eb").pack(fill="x", padx=20)

        info_form = ctk.CTkFrame(info_card, fg_color="transparent")
        info_form.pack(fill="x", padx=20, pady=15)
        info_form.grid_columnconfigure(1, weight=1)

        pad = {"padx": 15, "pady": 6}

        # DB Path
        db_path_display = DB_PATH if os.path.exists(DB_PATH) else "غير موجود"
        ctk.CTkLabel(info_form, text="مسار قاعدة البيانات:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=0, column=0, sticky="e", **pad)
        ctk.CTkLabel(info_form, text=db_path_display, font=("Segoe UI", 12),
                      text_color=TEXT_SEC, anchor="w").grid(row=0, column=1, sticky="w", **pad)

        # DB Size
        db_size = "-"
        if os.path.exists(DB_PATH):
            size_bytes = os.path.getsize(DB_PATH)
            if size_bytes < 1024:
                db_size = f"{size_bytes} بايت"
            elif size_bytes < 1024 * 1024:
                db_size = f"{size_bytes / 1024:.1f} كيلوبايت"
            else:
                db_size = f"{size_bytes / (1024 * 1024):.2f} ميجابايت"

        ctk.CTkLabel(info_form, text="حجم قاعدة البيانات:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=1, column=0, sticky="e", **pad)
        ctk.CTkLabel(info_form, text=db_size, font=("Segoe UI", 12),
                      text_color=TEXT_SEC, anchor="w").grid(row=1, column=1, sticky="w", **pad)

        # Version
        ctk.CTkLabel(info_form, text="إصدار البرنامج:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=2, column=0, sticky="e", **pad)
        ctk.CTkLabel(info_form, text="v1.0.0", font=("Segoe UI", 12, "bold"),
                      text_color=PRIMARY, anchor="w").grid(row=2, column=1, sticky="w", **pad)

        # Reset DB card
        reset_card = ctk.CTkFrame(self.content, fg_color=CARD_BG, corner_radius=12)
        reset_card.pack(fill="x", pady=15)

        ctk.CTkLabel(
            reset_card, text="⚠️ منطقة الخطر",
            font=("Segoe UI", 16, "bold"), text_color=DANGER, anchor="e"
        ).pack(fill="x", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            reset_card, text="سيتم حذف جميع البيانات وإعادة تعيين قاعدة البيانات بالكامل.",
            font=("Segoe UI", 12), text_color=TEXT_SEC, anchor="e"
        ).pack(fill="x", padx=20, pady=(0, 10))

        btn_frame = ctk.CTkFrame(reset_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_frame, text="🗑️ إعادة تعيين قاعدة البيانات", height=38, corner_radius=8,
            font=("Segoe UI", 13, "bold"), fg_color=DANGER, hover_color="#dc2626",
            command=self._reset_db
        ).pack(anchor="e", padx=15)

    def _reset_db(self):
        if not messagebox.askyesno(
            "⚠️ تحذير خطير",
            "هل أنت متأكد تماماً؟\n\n"
            "سيتم حذف جميع البيانات نهائياً:\n"
            "• العملاء والجلسات\n"
            "• الفواتير والمدفوعات\n"
            "• البطولات والحجوزات\n"
            "• الألعاب والباقات\n"
            "• المخزون والموظفين\n\n"
            "لا يمكن التراجع عن هذا الإجراء!",
            parent=self.winfo_toplevel()
        ):
            return

        # Double confirmation
        if not messagebox.askyesno(
            "تأكيد أخير",
            "اضغط \"نعم\" للتأكيد النهائي أو \"لا\" للإلغاء.",
            parent=self.winfo_toplevel()
        ):
            return

        try:
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            init_db()
            messagebox.showinfo("تم", "تم إعادة تعيين قاعدة البيانات بنجاح ✅",
                                parent=self.winfo_toplevel())
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء إعادة التعيين: {e}",
                                 parent=self.winfo_toplevel())

    # ── Refresh ──
    def refresh(self):
        current_tab = self.seg.get()
        self._show_tab(current_tab)