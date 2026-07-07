from main import *
from database.db import SessionLocal
from services.services import (
    create_tournament, get_tournaments, register_participant,
    get_tournament_participants, update_tournament_status,
    eliminate_participant, get_customers
)
from datetime import datetime
from tkinter import messagebox


# ─── Dialog: Create Tournament ─────────────────────────────
class CreateTournamentDialog(ctk.CTkToplevel):
    """نافذة إنشاء بطولة جديدة"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("إنشاء بطولة")
        self.geometry("480x460")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result = None

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 480) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 460) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 20, "pady": 7}

        ctk.CTkLabel(
            self, text="🏆 إنشاء بطولة جديدة",
            font=("Segoe UI", 18, "bold"), text_color=TEXT
        ).pack(pady=(20, 10))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=5)

        # Name
        ctk.CTkLabel(form, text="اسم البطولة:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=0, column=0, sticky="e", **pad)
        self.name_entry = ctk.CTkEntry(form, width=280, height=36,
                                        font=("Segoe UI", 12), placeholder_text="مثال: بطولة FIFA 2024")
        self.name_entry.grid(row=0, column=1, sticky="w", **pad)

        # Game
        ctk.CTkLabel(form, text="اللعبة:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=1, column=0, sticky="e", **pad)
        self.game_entry = ctk.CTkEntry(form, width=280, height=36,
                                        font=("Segoe UI", 12), placeholder_text="مثال: FIFA 24")
        self.game_entry.grid(row=1, column=1, sticky="w", **pad)

        # Max Players
        ctk.CTkLabel(form, text="الحد الأقصى للاعبين:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=2, column=0, sticky="e", **pad)
        self.max_entry = ctk.CTkEntry(form, width=280, height=36,
                                       font=("Segoe UI", 12), placeholder_text="16")
        self.max_entry.grid(row=2, column=1, sticky="w", **pad)

        # Entry Fee
        ctk.CTkLabel(form, text="رسوم الدخول (ج.م):", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=3, column=0, sticky="e", **pad)
        self.fee_entry = ctk.CTkEntry(form, width=280, height=36,
                                       font=("Segoe UI", 12), placeholder_text="0.00")
        self.fee_entry.grid(row=3, column=1, sticky="w", **pad)

        # Prize
        ctk.CTkLabel(form, text="الجائزة:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=4, column=0, sticky="e", **pad)
        self.prize_entry = ctk.CTkEntry(form, width=280, height=36,
                                         font=("Segoe UI", 12), placeholder_text="مثال: 500 ج.م")
        self.prize_entry.grid(row=4, column=1, sticky="w", **pad)

        # Start Date
        ctk.CTkLabel(form, text="تاريخ البداية:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").grid(row=5, column=0, sticky="e", **pad)
        self.date_entry = ctk.CTkEntry(form, width=280, height=36,
                                        font=("Segoe UI", 12),
                                        placeholder_text="YYYY-MM-DD HH:MM")
        self.date_entry.grid(row=5, column=1, sticky="w", **pad)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(10, 20))

        ctk.CTkButton(
            btn_frame, text="إلغاء", width=120, height=38,
            font=("Segoe UI", 13), fg_color=SECONDARY, hover_color=SECONDARY_HOVER,
            command=self._cancel
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            btn_frame, text="🏆 إنشاء", width=140, height=38,
            font=("Segoe UI", 13, "bold"), fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            command=self._save
        ).pack(side="right", padx=8)

    def _cancel(self):
        self.result = None
        self.destroy()

    def _save(self):
        name = self.name_entry.get().strip()
        game = self.game_entry.get().strip()
        if not name or not game:
            messagebox.showwarning("تحذير", "يرجى إدخال اسم البطولة واللعبة", parent=self)
            return

        try:
            max_players = int(self.max_entry.get().strip()) if self.max_entry.get().strip() else 16
            entry_fee = float(self.fee_entry.get().strip()) if self.fee_entry.get().strip() else 0.0
        except ValueError:
            messagebox.showwarning("تحذير", "يرجى إدخال أرقام صحيحة", parent=self)
            return

        prize = self.prize_entry.get().strip() or None
        date_str = self.date_entry.get().strip()

        try:
            start_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showwarning("تحذير", "صيغة التاريخ غير صحيحة (YYYY-MM-DD HH:MM)", parent=self)
            return

        self.result = {
            "name": name, "game": game, "max_players": max_players,
            "entry_fee": entry_fee, "prize": prize, "start_date": start_date
        }
        self.destroy()


# ─── Dialog: Register Participant ──────────────────────────
class RegisterDialog(ctk.CTkToplevel):
    """نافذة تسجيل لاعب في بطولة"""

    def __init__(self, parent, customers):
        super().__init__(parent)
        self.title("تسجيل لاعب")
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result = None
        self._customers = {c.name: c.id for c in customers}

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 200) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="👤 تسجيل لاعب",
            font=("Segoe UI", 18, "bold"), text_color=TEXT
        ).pack(pady=(20, 15))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=5)

        ctk.CTkLabel(form, text="اختر العميل:", font=("Segoe UI", 13),
                      text_color=TEXT, anchor="e").pack(anchor="e", pady=(5, 4))

        self.combo = ctk.CTkComboBox(
            form, values=list(self._customers.keys()), width=320, height=36,
            font=("Segoe UI", 12)
        )
        self.combo.pack(anchor="e", pady=(0, 10))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(5, 20))

        ctk.CTkButton(
            btn_frame, text="إلغاء", width=120, height=38,
            font=("Segoe UI", 13), fg_color=SECONDARY, hover_color=SECONDARY_HOVER,
            command=self._cancel
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            btn_frame, text="✅ تسجيل", width=140, height=38,
            font=("Segoe UI", 13, "bold"), fg_color=SUCCESS, hover_color=SUCCESS_HOVER,
            command=self._save
        ).pack(side="right", padx=8)

    def _cancel(self):
        self.result = None
        self.destroy()

    def _save(self):
        name = self.combo.get()
        if not name or name not in self._customers:
            messagebox.showwarning("تحذير", "يرجى اختيار عميل", parent=self)
            return
        self.result = {"customer_id": self._customers[name]}
        self.destroy()


# ─── Dialog: Participants List ─────────────────────────────
class ParticipantsDialog(ctk.CTkToplevel):
    """نافذة عرض المشاركين في بطولة"""

    def __init__(self, parent, tournament_id, tournament_name):
        super().__init__(parent)
        self.title(f"المشاركون - {tournament_name}")
        self.geometry("650x480")
        self.transient(parent)
        self.grab_set()
        self.tournament_id = tournament_id

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 650) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 480) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()
        self._load_participants()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="👥 المشاركون",
            font=("Segoe UI", 18, "bold"), text_color=TEXT
        ).pack(pady=(20, 10))

        # Header
        hdr = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=8)
        hdr.pack(fill="x", padx=20, pady=(0, 5))

        for col, (txt, w) in enumerate([
            ("المركز", 80), ("الاسم", 180), ("الحالة", 120), ("إجراء", 100)
        ]):
            ctk.CTkLabel(
                hdr, text=txt, font=("Segoe UI", 12, "bold"),
                text_color=TEXT, width=w, anchor="center"
            ).grid(row=0, column=col, padx=8, pady=8)

        # Scrollable list
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", height=320)
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=5)

    def _load_participants(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        db = SessionLocal()
        try:
            participants = get_tournament_participants(db, self.tournament_id)
        finally:
            db.close()

        if not participants:
            ctk.CTkLabel(
                self.list_frame, text="لا يوجد مشاركون بعد",
                font=("Segoe UI", 14), text_color=TEXT_SEC
            ).pack(pady=30)
            return

        for p in participants:
            name = p.customer.name if p.customer else f"عميل #{p.customer_id}"
            status_text = "مُقصى ❌" if p.is_eliminated else "نشط ✅"
            status_color = DANGER if p.is_eliminated else SUCCESS

            row = ctk.CTkFrame(self.list_frame, fg_color=CARD_BG, corner_radius=8)
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(
                row, text=str(p.bracket_position or "-"),
                font=("Segoe UI", 12), text_color=TEXT, width=80, anchor="center"
            ).grid(row=0, column=0, padx=8, pady=8)

            ctk.CTkLabel(
                row, text=name,
                font=("Segoe UI", 12), text_color=TEXT, width=180, anchor="center"
            ).grid(row=0, column=1, padx=8, pady=8)

            ctk.CTkLabel(
                row, text=status_text,
                font=("Segoe UI", 12, "bold"), text_color="white",
                fg_color=status_color, width=120, anchor="center", corner_radius=6
            ).grid(row=0, column=2, padx=8, pady=8)

            if not p.is_eliminated:
                ctk.CTkButton(
                    row, text="إقصاء", fg_color=DANGER, hover_color=DANGER_HOVER,
                    width=80, height=28, font=("Segoe UI", 11),
                    command=lambda pid=p.id: self._eliminate(pid)
                ).grid(row=0, column=3, padx=8, pady=8)

    def _eliminate(self, participant_id):
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من إقصاء هذا اللاعب؟",
                                    parent=self):
            return
        db = SessionLocal()
        try:
            eliminate_participant(db, participant_id)
        finally:
            db.close()
        self._load_participants()


# ─── Tournament Card ────────────────────────────────────────
class TournamentCard(ctk.CTkFrame):
    """بطاقة بطولة واحدة"""

    def __init__(self, master, tournament, on_register=None,
                 on_participants=None, on_status_change=None):
        super().__init__(master, fg_color=CARD_BG, corner_radius=12)
        self.tournament = tournament
        self.on_register = on_register
        self.on_participants = on_participants
        self.on_status_change = on_status_change
        self._build()

    def _build(self):
        t = self.tournament

        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            header, text=f"🏆 {t.name}",
            font=("Segoe UI", 16, "bold"), text_color=TEXT, anchor="e"
        ).pack(side="right", fill="x", expand=True)

        # Status chip
        status_color = STATUS_COLORS.get(t.status, TEXT_SEC)
        status_label = STATUS_LABELS.get(t.status, t.status)
        ctk.CTkLabel(
            header, text=f"  {status_label}  ",
            fg_color=status_color, text_color="white",
            font=("Segoe UI", 11, "bold"), corner_radius=6
        ).pack(side="left", padx=5)

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=DIVIDER).pack(fill="x", padx=15, pady=4)

        # Details
        details = ctk.CTkFrame(self, fg_color="transparent")
        details.pack(fill="x", padx=15, pady=(0, 4))

        registered = len(t.participants) if hasattr(t, 'participants') and t.participants else 0

        info_items = [
            ("🎮", t.game),
            ("💰", f"رسوم: {fc(t.entry_fee)}"),
            ("🏅", f"الجائزة: {t.prize or '-'}"),
            ("👥", f"{registered}/{t.max_players}"),
            ("📅", fmt_dt(t.start_date)),
        ]

        for icon, text in info_items:
            ctk.CTkLabel(
                details, text=f"{icon} {text}",
                font=("Segoe UI", 12), text_color=TEXT_SEC, anchor="e"
            ).pack(side="right", padx=(0, 12))

        # Buttons row
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(6, 12))

        ctk.CTkButton(
            btn_frame, text="👥 المشاركون", fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            width=110, height=32, font=("Segoe UI", 12),
            command=lambda: self.on_participants(t) if self.on_participants else None
        ).pack(side="right", padx=4)

        if t.status == "registration":
            ctk.CTkButton(
                btn_frame, text="✅ تسجيل لاعب", fg_color=SUCCESS, hover_color=SUCCESS_HOVER,
                width=120, height=32, font=("Segoe UI", 12),
                command=lambda: self.on_register(t) if self.on_register else None
            ).pack(side="right", padx=4)

        if t.status == "registration":
            ctk.CTkButton(
                btn_frame, text="▶️ بدء", fg_color=WARNING, hover_color=WARNING_HOVER,
                text_color="black", width=90, height=32, font=("Segoe UI", 12, "bold"),
                command=lambda: self.on_status_change(t.id, "in_progress")
                         if self.on_status_change else None
            ).pack(side="left", padx=4)

        elif t.status == "in_progress":
            ctk.CTkButton(
                btn_frame, text="✅ إكمال", fg_color=SUCCESS, hover_color=SUCCESS_HOVER,
                width=90, height=32, font=("Segoe UI", 12, "bold"),
                command=lambda: self.on_status_change(t.id, "completed")
                         if self.on_status_change else None
            ).pack(side="left", padx=4)


# ─── Tournaments Page ──────────────────────────────────────
class TournamentsPage(BasePage):
    """صفحة إدارة البطولات"""

    def __init__(self, master, app):
        super().__init__(master, app, title="البطولات")
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            header, text="🏆 إدارة البطولات",
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

        ctk.CTkButton(
            inner, text="➕ إنشاء بطولة", height=36, corner_radius=8,
            font=("Segoe UI", 13, "bold"), fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            command=self._create_tournament
        ).pack(side="left")

        # Cards container
        self.cards_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="both", expand=True)

        # Empty label
        self.empty_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 14), text_color=TEXT_SEC
        )

    def _clear_cards(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()
        self.empty_label.pack_forget()

    def _render_cards(self, tournaments):
        self._clear_cards()

        if not tournaments:
            self.empty_label.configure(text="لا توجد بطولات حالياً")
            self.empty_label.pack(pady=40)
            return

        for t in tournaments:
            card = TournamentCard(
                self.cards_frame, t,
                on_register=self._register_player,
                on_participants=self._show_participants,
                on_status_change=self._change_status,
            )
            card.pack(fill="x", pady=5)

    # ── Create Tournament ──
    def _create_tournament(self):
        dialog = CreateTournamentDialog(self.winfo_toplevel())
        self.wait_window(dialog)

        if dialog.result:
            db = SessionLocal()
            try:
                create_tournament(db, **dialog.result)
                self.refresh()
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                     parent=self.winfo_toplevel())
            finally:
                db.close()

    # ── Register Player ──
    def _register_player(self, tournament):
        db = SessionLocal()
        try:
            customers = get_customers(db)
        finally:
            db.close()

        if not customers:
            messagebox.showwarning("تنبيه", "لا يوجد عملاء مسجلين",
                                   parent=self.winfo_toplevel())
            return

        dialog = RegisterDialog(self.winfo_toplevel(), customers)
        self.wait_window(dialog)

        if dialog.result:
            db = SessionLocal()
            try:
                register_participant(db, tournament.id, dialog.result["customer_id"])
                self.refresh()
                messagebox.showinfo("تم", "تم تسجيل اللاعب بنجاح",
                                    parent=self.winfo_toplevel())
            except ValueError as e:
                messagebox.showwarning("تنبيه", str(e),
                                       parent=self.winfo_toplevel())
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                     parent=self.winfo_toplevel())
            finally:
                db.close()

    # ── Show Participants ──
    def _show_participants(self, tournament):
        ParticipantsDialog(self.winfo_toplevel(), tournament.id, tournament.name)

    # ── Change Status ──
    def _change_status(self, tournament_id, new_status):
        label = STATUS_LABELS.get(new_status, new_status)
        if not messagebox.askyesno("تأكيد", f"هل تريد تغيير حالة البطولة إلى \"{label}\"؟",
                                    parent=self.winfo_toplevel()):
            return
        db = SessionLocal()
        try:
            update_tournament_status(db, tournament_id, new_status)
            self.refresh()
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}",
                                 parent=self.winfo_toplevel())
        finally:
            db.close()

    # ── Refresh ──
    def refresh(self):
        db = SessionLocal()
        try:
            tournaments = get_tournaments(db)
            self.count_label.configure(text=f"إجمالي: {len(tournaments)} بطولة")
            self._render_cards(tournaments)
        finally:
            db.close()