from main import *
from services.services import get_active_sessions
from datetime import datetime


class DashboardPage(BasePage):
    """لوحة التحكم الرئيسية"""

    def __init__(self, master, app):
        super().__init__(master, app, title="لوحة التحكم")
        self._build_ui()

    def _build_ui(self):
        # ── عنوان الصفحة ──
        ctk.CTkLabel(
            self, text="📊 لوحة التحكم", font=("Segoe UI", 22, "bold"),
            text_color=TEXT, anchor="e"
        ).pack(fill="x", pady=(0, 15))

        # ── بطاقات الإحصائيات ──
        self.stats_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_grid.pack(fill="x", pady=(0, 20))
        self.stats_grid.grid_columnconfigure((0, 1, 2), weight=1)

        # ── قسم الجلسات النشطة ──
        ctk.CTkLabel(
            self, text="🟢 الجلسات النشطة حالياً",
            font=("Segoe UI", 16, "bold"), text_color=TEXT, anchor="e"
        ).pack(fill="x", pady=(0, 10))

        self.sessions_container = ctk.CTkFrame(self, fg_color="transparent")
        self.sessions_container.pack(fill="both", expand=True)

        self.stat_cards = []
        self._create_stat_cards()

    def _create_stat_cards(self):
        """إنشاء 6 بطاقات إحصائية في شبكة 3×2"""
        card_configs = [
            ("💰", "إيرادات اليوم", "0.00 ج.م", SUCCESS),
            ("📈", "إيرادات الأسبوع", "0.00 ج.م", PRIMARY),
            ("🎮", "محطات شغالة", "0 / 0", DANGER),
            ("📋", "جلسات اليوم", "0", "#3b82f6"),
            ("⏱️", "ساعات اللعب اليوم", "0.0 ساعة", WARNING),
            ("👥", "إجمالي العملاء", "0", "#8b5cf6"),
        ]

        self.stat_cards = []
        for idx, (icon, title, default_val, color) in enumerate(card_configs):
            row = idx // 3
            col = idx % 3

            card = ctk.CTkFrame(self.stats_grid, fg_color=CARD_BG, corner_radius=12)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            # أيقونة + لون
            icon_label = ctk.CTkLabel(
                card, text=icon, font=("", 28),
                text_color=color, anchor="w"
            )
            icon_label.pack(anchor="w", padx=15, pady=(12, 0))

            # القيمة
            val_label = ctk.CTkLabel(
                card, text=default_val, font=("Segoe UI", 20, "bold"),
                text_color=TEXT, anchor="w"
            )
            val_label.pack(anchor="w", padx=15, pady=(4, 0))

            # العنوان
            ctk.CTkLabel(
                card, text=title, font=("Segoe UI", 12),
                text_color=TEXT_SEC, anchor="w"
            ).pack(anchor="w", padx=15, pady=(2, 12))

            self.stat_cards.append(val_label)

    def _clear_sessions(self):
        """مسح قائمة الجلسات النشطة"""
        for widget in self.sessions_container.winfo_children():
            widget.destroy()

    def _show_empty_sessions(self):
        """عرض رسالة لا توجد جلسات"""
        self._clear_sessions()
        ctk.CTkLabel(
            self.sessions_container, text="لا توجد جلسات نشطة حالياً ✓",
            font=("Segoe UI", 14), text_color=TEXT_SEC
        ).pack(pady=30)

    def _show_sessions(self, active):
        """عرض قائمة الجلسات النشطة"""
        self._clear_sessions()

        # رأس الجدول
        header = ctk.CTkFrame(self.sessions_container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 5))

        headers = [
            ("رقم الجلسة", 80),
            ("اسم العميل", 150),
            ("المحطة", 120),
            ("المدة", 80),
            ("وقت البدء", 140),
        ]
        for text, width in headers:
            ctk.CTkLabel(
                header, text=text, width=width, font=("Segoe UI", 12, "bold"),
                text_color=TEXT_SEC, anchor="e"
            ).pack(side="right", padx=8)

        ctk.CTkFrame(self.sessions_container, height=1, fg_color=DIVIDER).pack(fill="x", pady=(0, 8))

        # صفوف الجلسات
        now = datetime.now()
        for s in active:
            row = ctk.CTkFrame(self.sessions_container, fg_color=CARD_BG, corner_radius=8)
            row.pack(fill="x", pady=3, padx=2)

            customer_name = s.customer.name if s.customer else "زائر"
            station_name = s.station.name if s.station else f"محطة {s.station_id}"

            # حساب المدة
            dur_minutes = int((now - s.start_time).total_seconds() / 60)

            cells = [
                (f"#{s.id}", 80),
                (customer_name, 150),
                (station_name, 120),
                (fmt_dur(dur_minutes), 80),
                (fmt_dt(s.start_time), 140),
            ]
            for text, width in cells:
                ctk.CTkLabel(
                    row, text=text, width=width, font=("Segoe UI", 12),
                    text_color=TEXT, anchor="e", height=32
                ).pack(side="right", padx=8)

    def refresh(self):
        """تحديث بيانات لوحة التحكم"""
        db = SessionLocal()
        try:
            stats = get_dashboard_stats(db)
            active = get_active_sessions(db)

            # تحديث بطاقات الإحصائيات
            values = [
                fc(stats["today_revenue"]),
                fc(stats["week_revenue"]),
                f"{stats['active_sessions']} / {stats['station_stats']['total']}",
                str(stats["today_sessions"]),
                f"{stats['today_hours']} ساعة",
                str(stats["total_customers"]),
            ]
            for card, val in zip(self.stat_cards, values):
                card.configure(text=val)

            # تحديث قائمة الجلسات النشطة
            if active:
                self._show_sessions(active)
            else:
                self._show_empty_sessions()

        finally:
            db.close()