from main import *
from database.db import SessionLocal
from database.models import SessionStatus
from services.services import (
    start_session, end_session, cancel_session,
    get_sessions, get_active_sessions, get_session_by_id,
    get_stations, get_customers, get_packages,
    process_session_payment, get_games
)
from tkinter import messagebox
from datetime import datetime


# ─── Dialog: Start Session ──────────────────────────────────
class StartSessionDialog(ctk.CTkToplevel):
    """نافذة بدء جلسة جديدة"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("بدء جلسة جديدة")
        self.geometry("460x560")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result = None

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 460) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 560) // 2
        self.geometry(f"+{x}+{y}")

        self._load_data()
        self._build_ui()

    def _load_data(self):
        """تحميل بيانات المحطات المتاحة والعملاء والباقات والألعاب"""
        self.available_stations = []
        self.all_customers = []
        self.all_packages = []
        self.all_games = []

        db = SessionLocal()
        try:
            self.available_stations = get_stations(db, status="available")
            self.all_customers = get_customers(db, active_only=True)
            self.all_packages = get_packages(db, active_only=True)
            self.all_games = get_games(db)
        finally:
            db.close()

    def _build_ui(self):
        pad = {"padx": 20, "pady": 6}

        # Title
        ctk.CTkLabel(
            self, text="▶️ بدء جلسة جديدة",
            font=("Segoe UI", 18, "bold"), text_color=TEXT
        ).pack(pady=(20, 10))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=5)

        # Station
        ctk.CTkLabel(
            form, text="المحطة:", font=("Segoe UI", 13),
            text_color=TEXT, anchor="e"
        ).grid(row=0, column=0, sticky="e", **pad)

        station_names = [s.name for s in self.available_stations]
        station_ids = [s.id for s in self.available_stations]
        self._station_ids = station_ids

        self.station_var = ctk.StringVar()
        self.station_combo = ctk.CTkComboBox(
            form, values=station_names, variable=self.station_var,
            width=280, height=38, font=("Segoe UI", 12)
        )
        self.station_combo.grid(row=0, column=1, sticky="w", **pad)

        # Customer
        ctk.CTkLabel(
            form, text="العميل:", font=("Segoe UI", 13),
            text_color=TEXT, anchor="e"
        ).grid(row=1, column=0, sticky="e", **pad)

        self._customer_names = ["زائر"] + [c.name for c in self.all_customers]
        customer_ids = [None] + [c.id for c in self.all_customers]
        self._customer_ids = customer_ids

        self.customer_var = ctk.StringVar(value="زائر")
        self.customer_combo = ctk.CTkComboBox(
            form, values=self._customer_names, variable=self.customer_var,
            width=280, height=38, font=("Segoe UI", 12)
        )
        self.customer_combo.grid(row=1, column=1, sticky="w", **pad)

        # Package (optional)
        ctk.CTkLabel(
            form, text="الباقة:", font=("Segoe UI", 13),
            text_color=TEXT, anchor="e"
        ).grid(row=2, column=0, sticky="e", **pad)

        self._package_names = ["بدون باقة"] + [
            f"{p.name} ({p.hours} ساعة - {fc(p.price)})"
            for p in self.all_packages
        ]
        package_ids = [None] + [p.id for p in self.all_packages]
        self._package_ids = package_ids

        self.package_var = ctk.StringVar(value="بدون باقة")
        self.package_combo = ctk.CTkComboBox(
            form, values=self._package_names, variable=self.package_var,
            width=280, height=38, font=("Segoe UI", 12)
        )
        self.package_combo.grid(row=2, column=1, sticky="w", **pad)
        self.package_combo.bind("<Button-1>", lambda e: None)

        # Game (optional)
        ctk.CTkLabel(
            form, text="اللعبة:", font=("Segoe UI", 13),
            text_color=TEXT, anchor="e"
        ).grid(row=3, column=0, sticky="e", **pad)

        self._game_names = ["بدون لعبة"] + [g.name for g in self.all_games]
        game_ids = [None] + [g.id for g in self.all_games]
        self._game_ids = game_ids

        self.game_var = ctk.StringVar(value="بدون لعبة")
        self.game_combo = ctk.CTkComboBox(
            form, values=self._game_names, variable=self.game_var,
            width=280, height=38, font=("Segoe UI", 12)
        )
        self.game_combo.grid(row=3, column=1, sticky="w", **pad)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(5, 20))

        ctk.CTkButton(
            btn_frame, text="إلغاء", width=120, height=38,
            font=("Segoe UI", 13), fg_color=SECONDARY, hover_color=SECONDARY_HOVER,
            command=self._cancel
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            btn_frame, text="▶ بدء الجلسة", width=160, height=38,
            font=("Segoe UI", 13, "bold"), fg_color=SUCCESS, hover_color=SUCCESS_HOVER,
            command=self._save
        ).pack(side="right", padx=8)

    def _cancel(self):
        self.result = None
        self.destroy()

    def _save(self):
        # Validate station
        station_name = self.station_var.get()
        if not station_name:
            messagebox.showwarning("تحذير", "يرجى اختيار المحطة", parent=self)
            return

        try:
            idx = [s.name for s in self.available_stations].index(station_name)
            station_id = self.available_stations[idx].id
        except (ValueError, IndexError):
            messagebox.showerror("خطأ", "المحطة المختارة غير صالحة", parent=self)
            return

        # Customer
        customer_name = self.customer_var.get()
        try:
            cidx = self._customer_names.index(customer_name)
            customer_id = self._customer_ids[cidx]
        except (ValueError, IndexError):
            customer_id = None

        # Package
        package_name = self.package_var.get()
        try:
            pidx = self._package_names.index(package_name)
            package_id = self._package_ids[pidx]
        except (ValueError, IndexError):
            package_id = None
        is_package = package_id is not None

        # Game
        game_name = self.game_var.get()
        try:
            gidx = self._game_names.index(game_name)
            game_id = self._game_ids[gidx]
        except (ValueError, IndexError):
            game_id = None
        game_ids = [game_id] if game_id else None

        self.result = {
            "station_id": station_id,
            "customer_id": customer_id,
            "is_package": is_package,
            "package_id": package_id,
            "game_ids": game_ids,
        }
        self.destroy()


# ─── Dialog: End Session ────────────────────────────────────
class EndSessionDialog(ctk.CTkToplevel):
    """نافذة إنهاء جلسة مع الدفع"""

    PAYMENT_METHODS = {
        "كاش": "cash",
        "فودافون كاش": "vodafone_cash",
        "إنستاباي": "instapay",
        "بطاقة بنكية": "bank_card",
        "محفظة": "wallet",
    }

    def __init__(self, parent, session_data):
        super().__init__(parent)
        self.title("إنهاء الجلسة")
        self.geometry("420x440")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result = None
        self.session_data = session_data

        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 420) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 440) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        sd = self.session_data
        pad = {"padx": 20, "pady": 6}

        ctk.CTkLabel(
            self, text="⏹️ إنهاء الجلسة",
            font=("Segoe UI", 18, "bold"), text_color=TEXT
        ).pack(pady=(20, 10))

        # Info frame
        info = ctk.CTkFrame(self, fg_color=INFO_BG, corner_radius=10)
        info.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(
            info, text=f"المدة:  {fmt_dur(sd['duration_minutes'])}",
            font=("Segoe UI", 14), text_color=TEXT, anchor="e"
        ).pack(fill="x", padx=15, pady=(10, 2))

        ctk.CTkLabel(
            info, text=f"التكلفة:  {fc(sd['total_cost'])}",
            font=("Segoe UI", 16, "bold"), text_color=PRIMARY, anchor="e"
        ).pack(fill="x", padx=15, pady=(2, 10))

        # Form
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=5)

        # Payment method
        ctk.CTkLabel(
            form, text="طريقة الدفع:", font=("Segoe UI", 13),
            text_color=TEXT, anchor="e"
        ).grid(row=0, column=0, sticky="e", **pad)

        self.payment_var = ctk.StringVar(value="كاش")
        self.payment_combo = ctk.CTkComboBox(
            form, values=list(self.PAYMENT_METHODS.keys()),
            variable=self.payment_var,
            width=240, height=38, font=("Segoe UI", 12)
        )
        self.payment_combo.grid(row=0, column=1, sticky="w", **pad)

        # Discount
        ctk.CTkLabel(
            form, text="الخصم (ج.م):", font=("Segoe UI", 13),
            text_color=TEXT, anchor="e"
        ).grid(row=1, column=0, sticky="e", **pad)

        self.discount_entry = ctk.CTkEntry(
            form, width=240, height=38,
            font=("Segoe UI", 12), placeholder_text="0.00"
        )
        self.discount_entry.grid(row=1, column=1, sticky="w", **pad)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(5, 20))

        ctk.CTkButton(
            btn_frame, text="إلغاء", width=120, height=38,
            font=("Segoe UI", 13), fg_color=SECONDARY, hover_color=SECONDARY_HOVER,
            command=self._cancel
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            btn_frame, text="✅ إنهاء وادفع", width=160, height=38,
            font=("Segoe UI", 13, "bold"), fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            command=self._save
        ).pack(side="right", padx=8)

    def _cancel(self):
        self.result = None
        self.destroy()

    def _save(self):
        try:
            discount = float(self.discount_entry.get()) if self.discount_entry.get().strip() else 0.0
        except ValueError:
            messagebox.showwarning("تحذير", "يرجى إدخال رقم صحيح للخصم", parent=self)
            return

        payment_method = self.PAYMENT_METHODS.get(self.payment_var.get(), "cash")

        self.result = {
            "payment_method": payment_method,
            "discount": discount,
        }
        self.destroy()


# ─── Active Session Card ────────────────────────────────────
class ActiveSessionCard(ctk.CTkFrame):
    """بطاقة جلسة نشطة"""

    def __init__(self, master, session, on_end=None, on_cancel=None):
        super().__init__(master, fg_color=CARD_BG, corner_radius=12)
        self.session = session
        self.on_end = on_end
        self.on_cancel = on_cancel
        self._build()

    def _build(self):
        s = self.session
        customer_name = s.customer.name if s.customer else "زائر"
        station_name = s.station.name if s.station else f"محطة {s.station_id}"
        now = datetime.now()
        dur_minutes = int((now - s.start_time).total_seconds() / 60)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(14, 4))

        ctk.CTkLabel(
            header, text=f"🎮 {station_name}",
            font=("Segoe UI", 15, "bold"), text_color=TEXT, anchor="e"
        ).pack(side="right", fill="x", expand=True)

        ctk.CTkLabel(
            header, text=f"#{s.id}",
            font=("Segoe UI", 11), text_color=TEXT_SEC, anchor="w"
        ).pack(side="left")

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=DIVIDER).pack(fill="x", padx=14, pady=4)

        # Customer
        ctk.CTkLabel(
            self, text=f"👤 {customer_name}",
            font=("Segoe UI", 13), text_color=TEXT, anchor="e"
        ).pack(fill="x", padx=14, pady=2)

        # Duration (live label stored for later updates)
        self.dur_label = ctk.CTkLabel(
            self, text=f"⏱️ المدة: {fmt_dur(dur_minutes)}",
            font=("Segoe UI", 13, "bold"), text_color=WARNING, anchor="e"
        )
        self.dur_label.pack(fill="x", padx=14, pady=2)

        # Start time
        ctk.CTkLabel(
            self, text=f"🕐 بدأت: {fmt_dt(s.start_time)}",
            font=("Segoe UI", 12), text_color=TEXT_SEC, anchor="e"
        ).pack(fill="x", padx=14, pady=2)

        # Package badge
        if s.is_package and s.package:
            ctk.CTkLabel(
                self, text=f"📦 باقة: {s.package.name}",
                font=("Segoe UI", 12), text_color="#8b5cf6", anchor="e"
            ).pack(fill="x", padx=14, pady=2)

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=DIVIDER).pack(fill="x", padx=14, pady=8)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=14, pady=(0, 14))

        ctk.CTkButton(
            btn_frame, text="⏹️ إنهاء", width=100, height=34,
            font=("Segoe UI", 12, "bold"), fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            corner_radius=8,
            command=lambda: self.on_end(self.session) if self.on_end else None
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btn_frame, text="❌ إلغاء", width=100, height=34,
            font=("Segoe UI", 12), fg_color=SECONDARY, hover_color=DANGER,
            corner_radius=8,
            command=lambda: self.on_cancel(self.session) if self.on_cancel else None
        ).pack(side="right", padx=4)


# ─── Sessions Page ──────────────────────────────────────────
class SessionsPage(BasePage):
    """صفحة إدارة الجلسات"""

    def __init__(self, master, app):
        super().__init__(master, app, title="الجلسات")
        self.active_sessions_list = []
        self.history_sessions_list = []
        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            header, text="▶️ إدارة الجلسات",
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

        # Segmented button for tabs
        self.tab_var = ctk.StringVar(value="الجلسات النشطة")
        self.seg_btn = ctk.CTkSegmentedButton(
            inner, values=["الجلسات النشطة", "سجل الجلسات"],
            variable=self.tab_var,
            font=("Segoe UI", 13, "bold"),
            command=self._on_tab_change,
            selected_color=PRIMARY,
            selected_hover_color=PRIMARY_HOVER,
        )
        self.seg_btn.pack(side="right", padx=(0, 10))

        # Start session button
        ctk.CTkButton(
            inner, text="▶ بدء جلسة", height=38, corner_radius=8,
            font=("Segoe UI", 13, "bold"), fg_color=SUCCESS, hover_color=SUCCESS_HOVER,
            command=self._start_session
        ).pack(side="left")

        # ── Content area (stacked frames) ──
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)

        # Active tab
        self.active_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.active_cards_grid = ctk.CTkScrollableFrame(self.active_frame, fg_color="transparent")
        self.active_cards_grid.pack(fill="both", expand=True)
        self.active_cards_grid.grid_columnconfigure((0, 1, 2), weight=1)

        # History tab
        self.history_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.history_container = ctk.CTkScrollableFrame(self.history_frame, fg_color="transparent")
        self.history_container.pack(fill="both", expand=True)

        # Empty labels
        self.empty_active = ctk.CTkLabel(
            self.active_frame, text="",
            font=("Segoe UI", 14), text_color=TEXT_SEC
        )
        self.empty_history = ctk.CTkLabel(
            self.history_frame, text="",
            font=("Segoe UI", 14), text_color=TEXT_SEC
        )

        # Show active tab by default
        self._show_active_tab()

    # ── Tab switching ──
    def _on_tab_change(self, value):
        if value == "الجلسات النشطة":
            self._show_active_tab()
        else:
            self._show_history_tab()

    def _show_active_tab(self):
        self.history_frame.pack_forget()
        self.empty_history.pack_forget()
        self.active_frame.pack(fill="both", expand=True)

    def _show_history_tab(self):
        self.active_frame.pack_forget()
        self.empty_active.pack_forget()
        self.history_frame.pack(fill="both", expand=True)

    # ── Start Session ──
    def _start_session(self):
        dialog = StartSessionDialog(self.winfo_toplevel())
        self.wait_window(dialog)

        if not dialog.result:
            return

        db = SessionLocal()
        try:
            result = dialog.result
            start_session(
                db,
                station_id=result["station_id"],
                customer_id=result["customer_id"],
                is_package=result["is_package"],
                package_id=result["package_id"],
                game_ids=result["game_ids"],
            )
            self.refresh()
        except ValueError as e:
            messagebox.showerror("خطأ", str(e), parent=self.winfo_toplevel())
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}", parent=self.winfo_toplevel())
        finally:
            db.close()

    # ── End Session ──
    def _end_session(self, session):
        db = SessionLocal()
        try:
            # End the session first to compute duration and cost
            ended = end_session(db, session.id)
        except ValueError as e:
            messagebox.showerror("خطأ", str(e), parent=self.winfo_toplevel())
            db.close()
            return
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}", parent=self.winfo_toplevel())
            db.close()
            return

        # Show payment dialog
        dialog = EndSessionDialog(self.winfo_toplevel(), {
            "duration_minutes": ended.duration_minutes or 0,
            "total_cost": ended.total_cost or 0,
        })
        self.wait_window(dialog)

        if dialog.result:
            try:
                process_session_payment(
                    db,
                    session_id=ended.id,
                    payment_method=dialog.result["payment_method"],
                    discount=dialog.result["discount"],
                )
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل في معالجة الدفع: {e}",
                                     parent=self.winfo_toplevel())

        db.close()
        self.refresh()

    # ── Cancel Session ──
    def _cancel_session(self, session):
        if not messagebox.askyesno(
            "تأكيد الإلغاء",
            f"هل أنت متأكد من إلغاء الجلسة #{session.id}؟\n"
            f"سيتم تحرير المحطة بدون أي رسوم.",
            parent=self.winfo_toplevel()
        ):
            return

        db = SessionLocal()
        try:
            cancel_session(db, session.id)
            self.refresh()
        except ValueError as e:
            messagebox.showerror("خطأ", str(e), parent=self.winfo_toplevel())
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}", parent=self.winfo_toplevel())
        finally:
            db.close()

    # ── Render active sessions ──
    def _clear_active(self):
        for widget in self.active_cards_grid.winfo_children():
            widget.destroy()
        self.empty_active.pack_forget()

    def _render_active(self, sessions):
        self._clear_active()

        if not sessions:
            self.empty_active.configure(text="لا توجد جلسات نشطة حالياً ✓")
            self.empty_active.pack(pady=40)
            return

        for idx, s in enumerate(sessions):
            row = idx // 3
            col = idx % 3
            card = ActiveSessionCard(
                self.active_cards_grid, s,
                on_end=self._end_session,
                on_cancel=self._cancel_session,
            )
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

    # ── Render history sessions ──
    def _clear_history(self):
        for widget in self.history_container.winfo_children():
            widget.destroy()
        self.empty_history.pack_forget()

    def _render_history(self, sessions):
        self._clear_history()

        if not sessions:
            self.empty_history.configure(text="لا توجد جلسات في السجل")
            self.empty_history.pack(pady=40)
            return

        # Table header
        header = ctk.CTkFrame(self.history_container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 5))

        headers = [
            ("العميل", 140),
            ("المحطة", 120),
            ("المدة", 90),
            ("التكلفة", 100),
            ("طريقة الدفع", 120),
            ("الحالة", 80),
            ("البداية", 150),
        ]
        for text, width in headers:
            ctk.CTkLabel(
                header, text=text, width=width,
                font=("Segoe UI", 11, "bold"), text_color=TEXT_SEC, anchor="e"
            ).pack(side="right", padx=4)

        ctk.CTkFrame(
            self.history_container, height=1, fg_color=DIVIDER
        ).pack(fill="x", pady=(0, 6))

        # Payment method labels
        pay_labels = {
            "cash": "كاش",
            "vodafone_cash": "فودافون كاش",
            "instapay": "إنستاباي",
            "bank_card": "بطاقة بنكية",
            "wallet": "محفظة",
        }

        # Rows
        for s in sessions:
            row = ctk.CTkFrame(self.history_container, fg_color=CARD_BG, corner_radius=8)
            row.pack(fill="x", pady=3, padx=2)

            customer_name = s.customer.name if s.customer else "زائر"
            station_name = s.station.name if s.station else f"محطة {s.station_id}"
            status_color = STATUS_COLORS.get(s.status, TEXT_SEC)
            status_text = STATUS_LABELS.get(s.status, s.status)

            # Get last payment method
            pay_method = "-"
            if s.payments:
                pm = s.payments[-1].payment_method
                pay_method = pay_labels.get(pm, pm)

            cells = [
                (customer_name, 140),
                (station_name, 120),
                (fmt_dur(s.duration_minutes), 90),
                (fc(s.total_cost or 0), 100),
                (pay_method, 120),
                (status_text, 80),
                (fmt_dt(s.start_time), 150),
            ]
            for text, width in cells:
                ctk.CTkLabel(
                    row, text=text, width=width,
                    font=("Segoe UI", 11), text_color=TEXT, anchor="e", height=32
                ).pack(side="right", padx=4)

            # Color the status cell
            if row.winfo_children():
                row.winfo_children()[-3].configure(text_color=status_color)

    # ── Refresh ──
    def refresh(self):
        db = SessionLocal()
        try:
            self.active_sessions_list = get_active_sessions(db)
            self.history_sessions_list = get_sessions(
                db, status=SessionStatus.COMPLETED.value
            )
            self.count_label.configure(
                text=f"نشطة: {len(self.active_sessions_list)}"
            )
            self._render_active(self.active_sessions_list)
            self._render_history(self.history_sessions_list)
        finally:
            db.close()