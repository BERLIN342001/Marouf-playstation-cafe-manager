import customtkinter as ctk
from main import *
from database.db import SessionLocal
from services.services import (
    get_revenue_report, get_station_usage_report,
    get_payment_method_report, get_top_customers_report
)
from utils.helpers import get_payment_label


class ReportsPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, app, "التقارير المالية")
        self.tab = 0

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
        toolbar.pack(fill="x", pady=(0, 10))
        seg = ctk.CTkSegmentedButton(toolbar,
            values=["الإيرادات", "المحطات", "طرق الدفع", "أفضل العملاء"],
            command=self._on_tab, font=("Segoe UI", 12))
        seg.set("الإيرادات")
        seg.pack(side="right", padx=10, pady=10)

        if self.tab == 0: self._revenue()
        elif self.tab == 1: self._stations()
        elif self.tab == 2: self._payments()
        elif self.tab == 3: self._customers()

    def _on_tab(self, val):
        tabs = {"الإيرادات": 0, "المحطات": 1, "طرق الدفع": 2, "أفضل العملاء": 3}
        self.tab = tabs.get(val, 0)
        self.refresh()

    def _revenue(self):
        db = SessionLocal()
        try:
            data = get_revenue_report(db, 30)
            total = sum(d["revenue"] for d in data)
            total_s = sum(d["sessions"] for d in data)

            summary = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
            summary.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(summary, text=f"إجمالي الإيرادات (30 يوم): {fc(total)}",
                          font=("Segoe UI", 16, "bold"), text_color=PRIMARY).pack(side="right", padx=20, pady=15)
            ctk.CTkLabel(summary, text=f"إجمالي الجلسات: {total_s}",
                          font=("Segoe UI", 14), text_color=TEXT_SEC).pack(side="right", padx=20, pady=15)

            header = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=8)
            header.pack(fill="x", pady=(0, 3))
            for txt, w in [("التاريخ", 200), ("الإيرادات", 200), ("جلسات", 100)]:
                ctk.CTkLabel(header, text=txt, font=("Segoe UI", 12, "bold"), width=w, anchor="e").pack(side="right", padx=10, pady=8)

            max_rev = max((d["revenue"] for d in data), default=1) or 1
            for d in data[-15:]:
                row = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=6)
                row.pack(fill="x", pady=1)
                ctk.CTkLabel(row, text=d["date"], font=("Segoe UI", 12), width=200, anchor="e").pack(side="right", padx=10, pady=6)
                color = SUCCESS if d["revenue"] > 0 else TEXT_SEC
                ctk.CTkLabel(row, text=fc(d["revenue"]), font=("Segoe UI", 12, "bold"), text_color=color, width=200, anchor="e").pack(side="right", padx=10, pady=6)
                ctk.CTkLabel(row, text=str(d["sessions"]), font=("Segoe UI", 12), width=100, anchor="e").pack(side="right", padx=10, pady=6)

                bar_w = int((d["revenue"] / max_rev) * 300) if d["revenue"] > 0 else 0
                if bar_w > 0:
                    bar = ctk.CTkFrame(row, width=bar_w, height=4, fg_color=PRIMARY, corner_radius=2)
                    bar.pack(side="left", padx=10, pady=6)
        finally:
            db.close()

    def _stations(self):
        db = SessionLocal()
        try:
            data = get_station_usage_report(db, 30)
            if not data:
                ctk.CTkLabel(self, text="لا توجد بيانات", font=("Segoe UI", 15), text_color=TEXT_SEC).pack(pady=40)
                return

            header = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=8)
            header.pack(fill="x", pady=(0, 3))
            for txt, w in [("المحطة", 150), ("جلسات", 100), ("ساعات", 120), ("الإيرادات", 200)]:
                ctk.CTkLabel(header, text=txt, font=("Segoe UI", 12, "bold"), width=w, anchor="e").pack(side="right", padx=10, pady=8)

            for d in sorted(data, key=lambda x: x["total_revenue"], reverse=True):
                row = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=6)
                row.pack(fill="x", pady=2)
                hrs = round(d["total_minutes"] / 60, 1)
                ctk.CTkLabel(row, text=f"محطة #{d['station_id']}", font=("Segoe UI", 12), width=150, anchor="e").pack(side="right", padx=10, pady=6)
                ctk.CTkLabel(row, text=str(d["total_sessions"]), font=("Segoe UI", 12), width=100, anchor="e").pack(side="right", padx=10, pady=6)
                ctk.CTkLabel(row, text=f"{hrs} ساعة", font=("Segoe UI", 12), width=120, anchor="e").pack(side="right", padx=10, pady=6)
                ctk.CTkLabel(row, text=fc(d["total_revenue"]), font=("Segoe UI", 12, "bold"), text_color=SUCCESS, width=200, anchor="e").pack(side="right", padx=10, pady=6)
        finally:
            db.close()

    def _payments(self):
        db = SessionLocal()
        try:
            data = get_payment_method_report(db, 30)
            if not data:
                ctk.CTkLabel(self, text="لا توجد بيانات", font=("Segoe UI", 15), text_color=TEXT_SEC).pack(pady=40)
                return

            for d in sorted(data, key=lambda x: x["total"], reverse=True):
                card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
                card.pack(fill="x", pady=4)
                ctk.CTkLabel(card, text="💳", font=("Segoe UI", 24)).pack(side="right", padx=15, pady=12)
                info = ctk.CTkFrame(card, fg_color="transparent")
                info.pack(side="right", fill="both", expand=True, padx=10, pady=12)
                ctk.CTkLabel(info, text=get_payment_label(d["method"]), font=("Segoe UI", 15, "bold"), text_color=TEXT, anchor="e").pack(fill="x")
                ctk.CTkLabel(info, text=f"{d['count']} عملية", font=("Segoe UI", 12), text_color=TEXT_SEC, anchor="e").pack(fill="x")
                ctk.CTkLabel(card, text=fc(d["total"]), font=("Segoe UI", 16, "bold"), text_color=SUCCESS).pack(side="left", padx=15, pady=12)
        finally:
            db.close()

    def _customers(self):
        db = SessionLocal()
        try:
            data = get_top_customers_report(db, 20)
            if not data:
                ctk.CTkLabel(self, text="لا توجد بيانات", font=("Segoe UI", 15), text_color=TEXT_SEC).pack(pady=40)
                return

            medals = ["🥇", "🥈", "🥉"]
            for i, d in enumerate(data):
                card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=8)
                card.pack(fill="x", pady=3)
                medal = medals[i] if i < 3 else f"  {i+1}."
                ctk.CTkLabel(card, text=medal, font=("Segoe UI", 18), width=50, anchor="e").pack(side="right", padx=10, pady=8)
                info = ctk.CTkFrame(card, fg_color="transparent")
                info.pack(side="right", fill="both", expand=True, padx=5, pady=8)
                ctk.CTkLabel(info, text=d["name"], font=("Segoe UI", 13, "bold"), text_color=TEXT, anchor="e").pack(fill="x")
                ctk.CTkLabel(info, text=d["phone"], font=("Segoe UI", 11), text_color=TEXT_SEC, anchor="e").pack(fill="x")
                ctk.CTkLabel(card, text=f"{d['total_sessions']} جلسة", font=("Segoe UI", 12), text_color=TEXT_SEC).pack(side="left", padx=10, pady=8)
                ctk.CTkLabel(card, text=fc(d["total_spent"]), font=("Segoe UI", 14, "bold"), text_color=PRIMARY).pack(side="left", padx=10, pady=8)
        finally:
            db.close()