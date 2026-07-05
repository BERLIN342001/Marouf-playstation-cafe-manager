import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from database.db import init_db, SessionLocal
from services.services import get_dashboard_stats
import os
import logging
import traceback

# ─── Debug Logging ──────────────────────────────────────────
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filemode="w",
    encoding="utf-8",
)
log = logging.getLogger("app")

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


# ════════════════════════════════════════════════════════════
#  App
# ════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Marouf - PlayStation Cafe Manager")
        self.geometry("1280x800")
        self.minsize(1024, 600)
        self.configure(fg_color=BG)

        self.pages = {}
        self.current_frame = None
        self._page_classes = {}

        try:
            self._build_sidebar()
            log.debug("Sidebar built OK")
        except Exception as e:
            log.error(f"Sidebar failed: {e}\n{traceback.format_exc()}")

        try:
            self._build_content()
            log.debug("Content area built OK")
        except Exception as e:
            log.error(f"Content area failed: {e}\n{traceback.format_exc()}")

        try:
            self._register_page_classes()
            log.debug("Page classes registered OK")
        except Exception as e:
            log.error(f"Page class registration failed: {e}\n{traceback.format_exc()}")

        try:
            self.show_page("dashboard")
            log.debug("Dashboard shown OK")
        except Exception as e:
            log.error(f"Dashboard show failed: {e}\n{traceback.format_exc()}")

    # ── Sidebar ──
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR_BG)

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=20, padx=16)

        ctk.CTkLabel(logo_frame, text="🎮", font=("", 36), text_color="white").pack()
        ctk.CTkLabel(logo_frame, text="Marouf", font=("Segoe UI", 20, "bold"),
                      text_color="white").pack(pady=(4, 0))
        ctk.CTkLabel(logo_frame, text="PlayStation Cafe", font=("Segoe UI", 11),
                      text_color="#9aa0a6").pack()

        ctk.CTkFrame(self.sidebar, height=1, fg_color="#3c4043").pack(fill="x", padx=10, pady=5)

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

    # ── Content Area ──
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

        # Pages container
        self.pages_frame = ctk.CTkFrame(self.content, corner_radius=0, fg_color=BG)
        self.pages_frame.pack(fill="both", expand=True)

    # ── Page Registration (lazy) ──
    def _register_page_classes(self):
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

        self._page_classes = {
            "dashboard": DashboardPage,
            "stations": StationsPage,
            "sessions": SessionsPage,
            "customers": CustomersPage,
            "billing": BillingPage,
            "inventory": InventoryPage,
            "employees": EmployeesPage,
            "reports": ReportsPage,
            "tournaments": TournamentsPage,
            "reservations": ReservationsPage,
            "settings": SettingsPage,
        }

    # ── Page Switching ──
    def show_page(self, key):
        log.info(f"show_page('{key}')")

        # Hide current
        if self.current_frame:
            try:
                self.current_frame.pack_forget()
            except Exception as e:
                log.error(f"pack_forget error: {e}")

        # Lazy create
        if key not in self.pages:
            log.info(f"Creating page '{key}' (lazy)...")
            try:
                cls = self._page_classes[key]
                self.pages[key] = cls(self.pages_frame, self)
                log.info(f"Page '{key}' created OK")
            except Exception as e:
                log.error(f"Page '{key}' creation FAILED: {e}\n{traceback.format_exc()}")
                err = ctk.CTkLabel(self.pages_frame,
                                   text=f"خطأ في تحميل الصفحة: {e}",
                                   font=("Segoe UI", 14), text_color=DANGER)
                err.pack(pady=40)
                self.current_frame = err
                return

        # Show
        try:
            self.current_frame = self.pages[key]
            self.current_frame.pack(fill="both", expand=True, padx=15, pady=15)
            self.current_frame.update_idletasks()

            titles = {
                "dashboard": "لوحة التحكم", "stations": "إدارة المحطات",
                "sessions": "إدارة الجلسات", "customers": "إدارة العملاء",
                "billing": "الفواتير والمدفوعات", "inventory": "إدارة المخزون",
                "employees": "إدارة الموظفين", "reports": "التقارير المالية",
                "tournaments": "إدارة البطولات", "reservations": "إدارة الحجوزات",
                "settings": "الإعدادات",
            }
            self.page_title_label.configure(text=titles.get(key, ""))

            self.pages[key].refresh()
            log.info(f"Page '{key}' shown + refreshed OK")
        except Exception as e:
            log.error(f"Page '{key}' show FAILED: {e}\n{traceback.format_exc()}")

        # Highlight nav
        for k, btn in self.nav_buttons.items():
            btn.configure(fg_color=PRIMARY if k == key else "transparent")


# ════════════════════════════════════════════════════════════
#  BasePage
# ════════════════════════════════════════════════════════════
class BasePage(ctk.CTkFrame):
    """Base class for all pages. Uses a regular CTkFrame for reliability."""

    def __init__(self, master, app, title=""):
        super().__init__(master, fg_color=BG)
        self.app = app
        self.title_text = title

    def refresh(self):
        pass


# ════════════════════════════════════════════════════════════
#  Entry Point
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    log.info("=== Application Starting ===")
    try:
        init_db()
        log.info("Database initialized OK")
    except Exception as e:
        log.error(f"Database init FAILED: {e}\n{traceback.format_exc()}")

    try:
        app = App()
        log.info("App created, starting mainloop")
        app.mainloop()
    except Exception as e:
        log.critical(f"FATAL: {e}\n{traceback.format_exc()}")
        try:
            messagebox.showerror("خطأ", f"حدث خطأ في تشغيل البرنامج:\n{e}")
        except:
            pass