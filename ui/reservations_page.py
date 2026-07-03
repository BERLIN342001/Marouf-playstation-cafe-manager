from main import *
from database.db import SessionLocal
from services.services import (
    create_reservation, get_reservations, update_reservation_status,
    get_customers, get_stations
)
from datetime import datetime
from tkinter import messagebox


# ─── Dialog: New Reservation ────────────────────────────────
class CreateReservationDialog(ctk.CTkToplevel):
    """نافذة إنشاء حجز جديد"""

    def __init__(self, parent, customers, available_stations):
        super().__init__(parent)
        self.title("حجز جديد")
        self.geometry("480x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result = None
        self._customers = {c.name: c.id for c in customers}
        self._stations = {s.name: s.id for s in available_stations}

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 480) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 520) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 20, "pady": 7}

        ctk.CTkLabel(
            self, text="📅 حجز جديد",
            font=("Segoe UI", 18, "bold"), text_color=TEXT
        ).pack(pady=(20, 10))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=5)

        # Customer
        ctk.CTkLabel(form, text="العميل:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=0, column=0, sticky="e", **pad)
        self.customer_combo = ctk.CTkComboBox(
            form, values=list(self._customers.keys()),
            width=280, height=36, font=("Segoe UI", 12)
        )
        self.customer_combo.grid(row=0, column=1, sticky="w", **pad)

        # Station
        ctk.CTkLabel(form, text="المحطة:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=1, column=0, sticky="e", **pad)
        station_values = list(self._stations.keys()) if self._stations else ["لا توجد محطات متاحة"]
        self.station_combo = ctk.CTkComboBox(
            form, values=station_values,
            width=280, height=36, font=("Segoe UI", 12)
        )
        self.station_combo.grid(row=1, column=1, sticky="w", **pad)

        # Date/Time
        ctk.CTkLabel(form, text="التاريخ والوقت:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=2, column=0, sticky="e", **pad)
        self.datetime_entry = ctk.CTkEntry(
            form, width=280, height=36, font=("Segoe UI", 12),
            placeholder_text="YYYY-MM-DD HH:MM"
        )
        self.datetime_entry.grid(row=2, column=1, sticky="w", **pad)
        self.datetime_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))

        # Duration
        ctk.CTkLabel(form, text="المدة (بالدقائق):", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=3, column=0, sticky="e", **pad)
        self.duration_entry = ctk.CTkEntry(
            form, width=280, height=36, font=("Segoe UI", 12),
            placeholder_text="60"
        )
        self.duration_entry.grid(row=3, column=1, sticky="w", **pad)
        self.duration_entry.insert(0, "60")

        # Notes
        ctk.CTkLabel(form, text="ملاحظات:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=4, column=0, sticky="ne", **pad)
        self.notes_entry = ctk.CTkTextbox(
            form, width=280, height=80, font=("Segoe UI", 12)
        )
        self.notes_entry.grid(row=4, column=1, sticky="w", **pad)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(10, 20))

        ctk.CTkButton(
            btn_frame, text="إلغاء", width=120, height=38,
            font=("Segoe UI", 13), fg_color="#9ca3af", hover_color="#6b7280",
            command=self._cancel
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            btn_frame, text="📅 إنشاء حجز", width=140, height=38,
            font=("Segoe UI", 13, "bold"), fg_color=PRIMARY, hover_color="#1557b0",
            command=self._save
        ).pack(side="right", padx=8)

    def _cancel(self):
        self.result = None
        self.destroy()

    def _save(self):
        customer_name = self.customer_combo.get()
        station_name = self.station_combo.get()

        if not customer_name or customer_name not in self._customers:
            messagebox.showwarning("تحذير", "يرجى اختيار عميل", parent=self)
            return

        if not station_name or station_name not in self._stations:
            messagebox.showwarning("تحذير", "يرجى اختيار محطة متاحة", parent=self)
            return

        date_str = self.datetime_entry.get().strip()
        try:
            reserved_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showwarning("تحذير", "صيغة التاريخ غير صحيحة (YYYY-MM-DD HH:MM)",
                                   parent=self)
            return

        try:
            duration = int(self.duration_entry.get().strip()) if self.duration_entry.get().strip() else 60
            if duration <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("تحذير", "يرجى إدخال مدة صحيحة (بالدقائق)", parent=self)
            return

        notes = self.notes_entry.get("1.0", "end").strip() or None

        self.result = {
            "customer_id": self._customers[customer_name],
            "station_id": self._stations[station_name],
            "reserved_date": reserved_date,
            "duration_minutes": duration,
            "notes": notes,
        }
        self.destroy()


# ─── Reservation Card ───────────────────────────────────────
class ReservationCard(ctk.CTkFrame):
    """بطاقة حجز واحد"""

    def __init__(self, master, reservation, on_confirm=None,
                 on_cancel=None, on_complete=None):
        super().__init__(master, fg_color=CARD_BG, corner_radius=12)
        self.reservation = reservation
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.on_complete = on_complete
        self._build()

    def _build(self):
        r = self.reservation

        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(12, 4))

        customer_name = r.customer.name if r.customer else f"عميل #{r.customer_id}"
        station_name = r.station.name if r.station else f"محطة #{r.station_id}"

        ctk.CTkLabel(
            header, text=f"👤 {customer_name}",
            font=("Segoe UI", 15, "bold"), text_color=TEXT, anchor="e"
        ).pack(side="right", fill="x", expand=True)

        # Status chip
        status_color = STATUS_COLORS.get(r.status, TEXT_SEC)
        status_label = STATUS_LABELS.get(r.status, r.status)
        ctk.CTkLabel(
            header, text=f"  {status_label}  ",
            fg_color=status_color, text_color="white",
            font=("Segoe UI", 11, "bold"), corner_radius=6
        ).pack(side="left", padx=5)

        # Separator
        ctk.CTkFrame(self, height=1, fg_color="#e5e7eb").pack(fill="x", padx=15, pady=4)

        # Details row
        details = ctk.CTkFrame(self, fg_color="transparent")
        details.pack(fill="x", padx=15, pady=(0, 4))

        info_items = [
            ("🎮", station_name),
            ("📅", fmt_dt(r.reserved_date)),
            ("⏱️", fmt_dur(r.duration_minutes)),
        ]

        for icon, text in info_items:
            ctk.CTkLabel(
                details, text=f"{icon} {text}",
                font=("Segoe UI", 12), text_color=TEXT_SEC, anchor="e"
            ).pack(side="right", padx=(0, 15))

        if r.notes:
            ctk.CTkLabel(
                self, text=f"📝 {r.notes}",
                font=("Segoe UI", 11), text_color=TEXT_SEC, anchor="e"
            ).pack(fill="x", padx=15, pady=(0, 4))

        # Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(6, 12))

        if r.status == "pending":
            ctk.CTkButton(
                btn_frame, text="✅ تأكيد", fg_color=PRIMARY, hover_color="#1557b0",
                width=100, height=32, font=("Segoe UI", 12),
                command=lambda: self.on_confirm(r.id) if self.on_confirm else None
            ).pack(side="right", padx=4)

            ctk.CTkButton(
                btn_frame, text="❌ إلغاء", fg_color=DANGER, hover_color="#dc2626",
                width=100, height=32, font=("Segoe UI", 12),
                command=lambda: self.on_cancel(r.id) if self.on_cancel else None
            ).pack(side="left", padx=4)

        elif r.status == "confirmed":
            ctk.CTkButton(
                btn_frame, text="✅ إكمال", fg_color=SUCCESS, hover_color="#16a34a",
                width=100, height=32, font=("Segoe UI", 12),
                command=lambda: self.on_complete(r.id) if self.on_complete else None
            ).pack(side="right", padx=4)

            ctk.CTkButton(
                btn_frame, text="❌ إلغاء", fg_color=DANGER, hover_color="#dc2626",
                width=100, height=32, font=("Segoe UI", 12),
                command=lambda: self.on_cancel(r.id) if self.on_cancel else None
            ).pack(side="left", padx=4)

        elif r.status == "completed":
            ctk.CTkLabel(
                btn_frame, text="تم تنفيذ الحجز بنجاح ✅",
                font=("Segoe UI", 12), text_color=SUCCESS
            ).pack(side="right")

        elif r.status == "cancelled":
            ctk.CTkLabel(
                btn_frame, text="تم إلغاء الحجز ❌",
                font=("Segoe UI", 12), text_color=DANGER
            ).pack(side="right")


# ─── Reservations Page ─────────────────────────────────────
class ReservationsPage(BasePage):
    """صفحة إدارة الحجوزات"""

    FILTER_MAP = {
        "الكل": None,
        "قيد الانتظار": "pending",
        "مؤكدة": "confirmed",
        "ملغاة": "cancelled",
        "مكتملة": "completed",
    }

    def __init__(self, master, app):
        super().__init__(master, app, title="الحجوزات")
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            header, text="📅 إدارة الحجوزات",
            font=("Segoe UI", 22, "bold"), text_color=TEXT, anchor="e"
        ).pack(side="right")

        self.count_label = ctk.CTkLabel(
            header, text="", font=("Segoe UI", 13),
            text_color=TEXT_SEC, anchor="e"
        )
        self.count_label.pack(side="left", padx=10)

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        toolbar.pack(fill="x", pady=(0, 15))

        inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        # Filter
        ctk.CTkLabel(
            inner, text="🔍", font=("", 16), anchor="e"
        ).pack(side="right", padx=(0, 6))

        self.filter_combo = ctk.CTkComboBox(
            inner, values=list(self.FILTER_MAP.keys()),
            width=180, height=36, font=("Segoe UI", 12),
            command=lambda _: self.refresh()
        )
        self.filter_combo.pack(side="right", padx=(0, 15))
        self.filter_combo.set("الكل")

        # New reservation button
        ctk.CTkButton(
            inner, text="➕ حجز جديد", height=36, corner_radius=8,
            font=("Segoe UI", 13, "bold"), fg_color=PRIMARY, hover_color="#1557b0",
            command=self._new_reservation
        ).pack(side="left")

        # Cards container
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="both", expand=True)

        # Empty label
        self.empty_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 14), text_color=TEXT_SEC
        )

    def _clear_cards(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()
        self.empty_label.pack_forget()

    def _render_cards(self, reservations):
        self._clear_cards()

        if not reservations:
            self.empty_label.configure(text="لا توجد حجوزات")
            self.empty_label.pack(pady=40)
            return

        for r in reservations:
            card = ReservationCard(
                self.cards_frame, r,
                on_confirm=self._confirm_reservation,
                on_cancel=self._cancel_reservation,
                on_complete=self._complete_reservation,
            )
            card.pack(fill="x", pady=5)

    # ── New Reservation ──
    def _new_reservation(self):
        db = SessionLocal()
        try:
            customers = get_customers(db)
            available_stations = get_stations(db, status="available")
        finally:
            db.close()

        if not customers:
            messagebox.showwarning("تنبيه", "لا يوجد عملاء مسجلين",
                                   parent=self.winfo_toplevel())
            return

        if not available_stations:
            messagebox.showwarning("تنبيه", "لا توجد محطات متاحة حالياً",
                                   parent=self.winfo_toplevel())
            return

        dialog = CreateReservationDialog(self.winfo_toplevel(), customers, available_stations)
        self.wait_window(dialog)

        if dialog.result:
            db = SessionLocal()
            try:
                create_reservation(db, **dialog.result)
                self.refresh()
                messagebox.showinfo("تم", "تم إنشاء الحجز بنجاح",
                                    parent=self.winfo_toplevel())
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                     parent=self.winfo_toplevel())
            finally:
                db.close()

    # ── Confirm Reservation ──
    def _confirm_reservation(self, reservation_id):
        if not messagebox.askyesno("تأكيد", "هل تريد تأكيد هذا الحجز؟",
                                    parent=self.winfo_toplevel()):
            return
        db = SessionLocal()
        try:
            update_reservation_status(db, reservation_id, "confirmed")
            self.refresh()
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                 parent=self.winfo_toplevel())
        finally:
            db.close()

    # ── Cancel Reservation ──
    def _cancel_reservation(self, reservation_id):
        if not messagebox.askyesno("تأكيد", "هل تريد إلغاء هذا الحجز؟",
                                    parent=self.winfo_toplevel()):
            return
        db = SessionLocal()
        try:
            update_reservation_status(db, reservation_id, "cancelled")
            self.refresh()
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                 parent=self.winfo_toplevel())
        finally:
            db.close()

    # ── Complete Reservation ──
    def _complete_reservation(self, reservation_id):
        if not messagebox.askyesno("تأكيد", "هل تريد إكمال هذا الحجز؟",
                                    parent=self.winfo_toplevel()):
            return
        db = SessionLocal()
        try:
            update_reservation_status(db, reservation_id, "completed")
            self.refresh()
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                 parent=self.winfo_toplevel())
        finally:
            db.close()

    # ── Refresh ──
    def refresh(self):
        filter_key = self.filter_combo.get()
        status = self.FILTER_MAP.get(filter_key)

        db = SessionLocal()
        try:
            reservations = get_reservations(db, status=status)
            self.count_label.configure(text=f"إجمالي: {len(reservations)} حجز")
            self._render_cards(reservations)
        finally:
            db.close()