from main import *
from database.db import SessionLocal
from services.services import get_daily_revenue, get_payments
from datetime import datetime, date
from tkinter import messagebox


def parse_date(date_str: str) -> date:
    """محاولة تحويل نص التاريخ إلى كائن date. ترجع None عند الفشل."""
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError, AttributeError):
        return None


# ─── Payment Row Card ────────────────────────────────────────
class PaymentRow(ctk.CTkFrame):
    """صف دفعة واحد في القائمة"""

    PAYMENT_LABELS = {
        "cash": "كاش",
        "vodafone_cash": "فودافون كاش",
        "instapay": "إنستاباي",
        "bank_card": "بطاقة بنكية",
        "wallet": "محفظة",
    }

    def __init__(self, master, payment):
        super().__init__(master, fg_color=CARD_BG, corner_radius=10)
        self.payment = payment
        self._build()

    def _build(self):
        p = self.payment

        # Customer name
        customer_name = p.customer.name if p.customer else "زائر"

        # Session reference
        if p.session:
            station_name = p.session.station.name if p.session.station else f"محطة {p.session.station_id}"
            session_ref = f"جلسة #{p.session_id} — {station_name}"
        else:
            session_ref = "—"

        # Payment method label
        pay_label = self.PAYMENT_LABELS.get(p.payment_method, p.payment_method)

        # Time of payment
        time_str = p.created_at.strftime("%H:%M") if p.created_at else ""

        # Top row: customer + time
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 2))

        ctk.CTkLabel(
            top, text=f"👤 {customer_name}",
            font=("Segoe UI", 14, "bold"), text_color=TEXT, anchor="e"
        ).pack(side="right", fill="x", expand=True)

        ctk.CTkLabel(
            top, text=f"🕐 {time_str}",
            font=("Segoe UI", 11), text_color=TEXT_SEC, anchor="w"
        ).pack(side="left")

        # Session reference
        ctk.CTkLabel(
            self, text=f"  {session_ref}",
            font=("Segoe UI", 12), text_color=TEXT_SEC, anchor="e"
        ).pack(fill="x", padx=14, pady=1)

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=DIVIDER).pack(fill="x", padx=14, pady=6)

        # Bottom row: payment method, amount, discount, final
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=14, pady=(0, 12))

        ctk.CTkLabel(
            bottom, text=f"💳 {pay_label}",
            font=("Segoe UI", 12), text_color=TEXT_SEC, anchor="w"
        ).pack(side="left", padx=(0, 16))

        ctk.CTkLabel(
            bottom, text=f"المبلغ: {fc(p.amount)}",
            font=("Segoe UI", 12), text_color=TEXT_SEC, anchor="w"
        ).pack(side="left", padx=(0, 16))

        if p.discount and p.discount > 0:
            ctk.CTkLabel(
                bottom, text=f"خصم: -{fc(p.discount)}",
                font=("Segoe UI", 12), text_color=DANGER, anchor="w"
            ).pack(side="left", padx=(0, 16))

        ctk.CTkLabel(
            bottom, text=f"الإجمالي: {fc(p.final_amount)}",
            font=("Segoe UI", 14, "bold"), text_color=PRIMARY, anchor="e"
        ).pack(side="right", fill="x", expand=True)


# ─── Billing Page ────────────────────────────────────────────
class BillingPage(BasePage):
    """صفحة الفواتير والإيرادات اليومية"""

    def __init__(self, master, app):
        super().__init__(master, app, title="الفواتير")
        self.payments_list = []
        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            header, text="🧾 الفواتير والإيرادات",
            font=("Segoe UI", 22, "bold"), text_color=TEXT, anchor="e"
        ).pack(side="right")

        # ── Date picker + show button ──
        toolbar = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        toolbar.pack(fill="x", pady=(0, 15))

        inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            inner, text="📅 التاريخ:",
            font=("Segoe UI", 13, "bold"), text_color=TEXT, anchor="e"
        ).pack(side="right", padx=(0, 8))

        self.date_entry = ctk.CTkEntry(
            inner, width=160, height=38,
            font=("Segoe UI", 13), placeholder_text="YYYY-MM-DD"
        )
        self.date_entry.pack(side="right", padx=(0, 10))
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ctk.CTkButton(
            inner, text="🔍 عرض", height=38, corner_radius=8,
            font=("Segoe UI", 13, "bold"), fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            command=self._on_date_change
        ).pack(side="right", padx=(0, 6))

        # ── Revenue card ──
        self.revenue_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14)
        self.revenue_card.pack(fill="x", pady=(0, 15))

        revenue_inner = ctk.CTkFrame(self.revenue_card, fg_color="transparent")
        revenue_inner.pack(fill="x", padx=20, pady=18)

        ctk.CTkLabel(
            revenue_inner, text="💰 إجمالي الإيرادات",
            font=("Segoe UI", 14), text_color=TEXT_SEC, anchor="e"
        ).pack(side="right", fill="x", expand=True)

        self.revenue_label = ctk.CTkLabel(
            revenue_inner, text="0.00 ج.م",
            font=("Segoe UI", 28, "bold"), text_color=SUCCESS, anchor="w"
        )
        self.revenue_label.pack(side="left")

        # ── Count label ──
        self.count_label = ctk.CTkLabel(
            self, text="",
            font=("Segoe UI", 13), text_color=TEXT_SEC, anchor="e"
        )
        self.count_label.pack(fill="x", pady=(0, 8))

        # ── Table header ──
        tbl_header = ctk.CTkFrame(self, fg_color="transparent")
        tbl_header.pack(fill="x", pady=(0, 5))

        headers = [
            ("العميل", 150),
            ("الجلسة", 200),
            ("طريقة الدفع", 110),
            ("المبلغ", 100),
            ("الخصم", 80),
            ("الإجمالي", 110),
        ]
        for text, width in headers:
            ctk.CTkLabel(
                tbl_header, text=text, width=width,
                font=("Segoe UI", 11, "bold"), text_color=TEXT_SEC, anchor="e"
            ).pack(side="right", padx=4)

        ctk.CTkFrame(self, height=1, fg_color=DIVIDER).pack(fill="x", pady=(0, 8))

        # ── Payments list container ──
        self.payments_container = ctk.CTkFrame(self, fg_color="transparent")
        self.payments_container.pack(fill="both", expand=True)

        # Empty label
        self.empty_label = ctk.CTkLabel(
            self, text="",
            font=("Segoe UI", 14), text_color=TEXT_SEC
        )

    def _on_date_change(self):
        self.refresh()

    def _clear_payments(self):
        for widget in self.payments_container.winfo_children():
            widget.destroy()
        self.empty_label.pack_forget()

    def _render_payments(self, payments):
        self._clear_payments()

        if not payments:
            self.empty_label.configure(text="لا توجد مدفوعات في هذا التاريخ")
            self.empty_label.pack(pady=40)
            return

        for p in payments:
            row = PaymentRow(self.payments_container, p)
            row.pack(fill="x", pady=3)

    # ── Refresh ──
    def refresh(self):
        date_str = self.date_entry.get().strip()
        selected_date = parse_date(date_str)

        if selected_date is None:
            self.revenue_label.configure(text="تاريخ غير صالح", text_color=DANGER)
            self.count_label.configure(text="")
            self._clear_payments()
            self.empty_label.configure(text="يرجى إدخال تاريخ صحيح بصيغة YYYY-MM-DD")
            self.empty_label.pack(pady=40)
            return

        db = SessionLocal()
        try:
            dt = datetime.combine(selected_date, datetime.min.time())
            total, self.payments_list = get_daily_revenue(db, date=dt)

            self.revenue_label.configure(text=fc(total), text_color=SUCCESS)
            self.count_label.configure(
                text=f"عدد المدفوعات: {len(self.payments_list)}"
            )
            self._render_payments(self.payments_list)
        except Exception as e:
            self.revenue_label.configure(text="خطأ", text_color=DANGER)
            messagebox.showerror("خطأ", f"حدث خطأ أثناء تحميل البيانات: {e}",
                                 parent=self.winfo_toplevel())
        finally:
            db.close()