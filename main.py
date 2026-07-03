import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database.db import init_db, SessionLocal
from services.services import get_dashboard_stats
import os

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

PRIMARY = "#1a73e8"
BG = "#f0f2f5"
SIDEBAR_BG = "#202124"
TEXT = "#202124"
TEXT_SEC = "#5f6368"
SUCCESS = "#22c55e"
DANGER = "#ef4444"
WARNING = "#f59e0b"
CARD_BG = "#ffffff"

STATUS_COLORS = {
    "available": SUCCESS, "occupied": DANGER,
    "maintenance": WARNING, "reserved": "#3b82f6",
    "active": SUCCESS, "completed": TEXT_SEC,
    "cancelled": DANGER, "pending": WARNING,
    "confirmed": "#3b82f6", "registration": "#3b82f6",
    "in_progress": SUCCESS,
}
STATUS_LABELS = {
    "available": "فارغة", "occupied": "مشغولة",
    "maintenance": "صيانة", "reserved": "محجوزة",
    "active": "نشطة", "completed": "مكتملة",
    "cancelled": "ملغاة", "pending": "قيد الانتظار",
    "confirmed": "مؤكدة", "registration": "تسجيل",
    "in_progress": "جارية",
}


def fc(amount):
    return f"{amount:.2f} ج.م"


def fmt_dur(minutes):
    if minutes is None:
        return "0:00"
    return f"{minutes // 60}:{minutes % 60:02d}"


def fmt_dt(dt):
    if dt is None:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Marouf - PlayStation Cafe Manager")
        self.geometry("1280x800")
        self.minsize(1024, 600)
        self.configure(fg_color=BG)

        self.pages = {}
        self.current_frame = None

        self._build_sidebar()
        self._build_content()
        self._load_all_pages()
        self.show_page("dashboard")

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR_BG)

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=20, padx=16)

        icon_label = ctk.CTkLabel(logo_frame, text="🎮", font=("", 36), text_color="white")
        icon_label.pack()

        ctk.CTkLabel(logo_frame, text="Marouf", font=("Segoe UI", 20, "bold"),
                      text_color="white").pack(pady=(4, 0))
        ctk.CTkLabel(logo_frame, text="PlayStation Cafe", font=("Segoe UI", 11),
                      text_color="#9aa0a6").pack()

        ctk.CTkFrame(self.sidebar, height=1, fg_color="#3c4043").pack(fill="x", padx=10, pady=5)

        # Nav buttons
        nav_items = [
            ("dashboard", "📊  لوحة التحكم"),
            ("stations", "🎮  المحطات"),
            ("sessions", "▶️  الجلسات"),
            ("customers", "👥  العملاء"),
            ("billing", "🧾  الفواتير"),
            ("inventory", "📦  المخزون"),
            ("employees", "👔  الموظفين"),
            ("reports", "📈  التقارير"),
            ("tournaments", "🏆  البطولات"),
            ("reservations", "📅  الحجوزات"),
            ("settings", "⚙️  الإعدادات"),
        ]

        self.nav_buttons = {}
        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=label, font=("Segoe UI", 13),
                fg_color="transparent", text_color="#e8eaed",
                anchor="w", height=42, corner_radius=10,
                hover_color="#3c4043",
                command=lambda k=key: self.show_page(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

        ctk.CTkFrame(self.sidebar, height=1, fg_color="#3c4043").pack(fill="x", padx=10, pady=5, side="bottom")
        ctk.CTkLabel(self.sidebar, text="v1.0", font=("Segoe UI", 10),
                      text_color="#9aa0a6").pack(side="bottom", pady=8)

        self.sidebar.pack(side="left", fill="y")

    def _build_content(self):
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=BG)
        self.content.pack(side="right", fill="both", expand=True, padx=0, pady=0)

        # Top bar
        self.topbar = ctk.CTkFrame(self.content, height=50, corner_radius=0, fg_color=CARD_BG)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)

        ctk.CTkLabel(self.topbar, text="Marouf PlayStation Cafe Manager",
                      font=("Segoe UI", 13), text_color=TEXT_SEC).pack(side="right", padx=20, pady=10)

        self.page_title_label = ctk.CTkLabel(self.topbar, text="", font=("Segoe UI", 13),
                                               text_color=TEXT_SEC)
        self.page_title_label.pack(side="left", padx=20, pady=10)

        # Content frame
        self.pages_frame = ctk.CTkFrame(self.content, corner_radius=0, fg_color=BG)
        self.pages_frame.pack(fill="both", expand=True)

    def _load_all_pages(self):
        from ui.dashboard import DashboardPage
        from ui.stations_page import StationsPage
        from ui.sessions_page import SessionsPage
        from ui.customers_page import CustomersPage
        from ui.billing_page import BillingPage
        from ui.inventory_page import InventoryPage
        from ui.employees_page import EmployeesPage
        from ui.reports_page import ReportsPage
        from ui.tournaments_page import TournamentsPage
        from ui.reservations_page import ReservationsPage
        from ui.settings_page import SettingsPage

        self.pages = {
            "dashboard": DashboardPage(self.pages_frame, self),
            "stations": StationsPage(self.pages_frame, self),
            "sessions": SessionsPage(self.pages_frame, self),
            "customers": CustomersPage(self.pages_frame, self),
            "billing": BillingPage(self.pages_frame, self),
            "inventory": InventoryPage(self.pages_frame, self),
            "employees": EmployeesPage(self.pages_frame, self),
            "reports": ReportsPage(self.pages_frame, self),
            "tournaments": TournamentsPage(self.pages_frame, self),
            "reservations": ReservationsPage(self.pages_frame, self),
            "settings": SettingsPage(self.pages_frame, self),
        }

    def show_page(self, key):
        if self.current_frame:
            self.current_frame.pack_forget()
        if key in self.pages:
            self.current_frame = self.pages[key]
            self.current_frame.pack(fill="both", expand=True, padx=15, pady=15)
            self.pages[key].refresh()

        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=PRIMARY)
            else:
                btn.configure(fg_color="transparent")


class BasePage(ctk.CTkScrollableFrame):
    def __init__(self, master, app, title=""):
        super().__init__(master, fg_color=BG)
        self.app = app
        self.title_text = title


if __name__ == "__main__":
    init_db()
    app = App()
    app.mainloop()