import os
import sys
import logging
import traceback

# ─── Ensure project directory is in path ────────────────────
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# ─── Debug Logging ──────────────────────────────────────────
LOG_FILE = os.path.join(PROJECT_DIR, "debug.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filemode="w",
    encoding="utf-8",
)
log = logging.getLogger("app")

# ─── Check Dependencies ─────────────────────────────────────
def check_dependencies():
    """Verify all required packages are installed."""
    missing = []
    try:
        import customtkinter
        log.info(f"customtkinter {customtkinter.__version__} OK")
    except ImportError:
        missing.append("customtkinter")
        log.error("customtkinter NOT installed!")

    try:
        import sqlalchemy
        log.info(f"sqlalchemy {sqlalchemy.__version__} OK")
    except ImportError:
        missing.append("SQLAlchemy")
        log.error("SQLAlchemy NOT installed!")

    return missing


# ─── Import after dependency check ──────────────────────────
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

from database.db import init_db, SessionLocal
from services.services import get_dashboard_stats, get_setting, set_setting
from themes import THEMES, THEME_ORDER


# ════════════════════════════════════════════════════════════
#  Theme Application — sets module-level color globals
# ════════════════════════════════════════════════════════════
def _apply_theme_colors(theme_name):
    """Update module-level color variables from a theme dict."""
    t = THEMES[theme_name]
    ctk.set_appearance_mode(t["mode"])

    # Module-level globals — pages read these via `from main import *`
    global PRIMARY, PRIMARY_HOVER, BG, SIDEBAR_BG, TEXT, TEXT_SEC
    global SUCCESS, SUCCESS_HOVER, DANGER, DANGER_HOVER, WARNING, WARNING_HOVER
    global SECONDARY, SECONDARY_HOVER
    global CARD_BG, DIVIDER, ROW_BG, DELETE_HOVER
    global SIDEBAR_TEXT, SIDEBAR_HOVER, SIDEBAR_DIVIDER, SIDEBAR_SUB, INFO_BG

    PRIMARY          = t["PRIMARY"]
    PRIMARY_HOVER    = t["PRIMARY_HOVER"]
    BG               = t["BG"]
    SIDEBAR_BG       = t["SIDEBAR_BG"]
    TEXT             = t["TEXT"]
    TEXT_SEC         = t["TEXT_SEC"]
    SUCCESS          = t["SUCCESS"]
    SUCCESS_HOVER    = t["SUCCESS_HOVER"]
    DANGER           = t["DANGER"]
    DANGER_HOVER     = t["DANGER_HOVER"]
    WARNING          = t["WARNING"]
    WARNING_HOVER    = t["WARNING_HOVER"]
    SECONDARY        = t["SECONDARY"]
    SECONDARY_HOVER  = t["SECONDARY_HOVER"]
    CARD_BG          = t["CARD_BG"]
    DIVIDER          = t["DIVIDER"]
    ROW_BG           = t["ROW_BG"]
    DELETE_HOVER     = t["DELETE_HOVER"]
    SIDEBAR_TEXT     = t["SIDEBAR_TEXT"]
    SIDEBAR_HOVER    = t["SIDEBAR_HOVER"]
    SIDEBAR_DIVIDER  = t["SIDEBAR_DIVIDER"]
    SIDEBAR_SUB      = t["SIDEBAR_SUB"]
    INFO_BG          = t["INFO_BG"]

    # Rebuild STATUS_COLORS with updated colors
    global STATUS_COLORS
    STATUS_COLORS = {
        "available": SUCCESS, "occupied": DANGER,
        "maintenance": WARNING, "reserved": PRIMARY,
        "active": SUCCESS, "completed": TEXT_SEC,
        "cancelled": DANGER, "pending": WARNING,
        "confirmed": PRIMARY, "registration": PRIMARY,
        "in_progress": SUCCESS,
    }

# ─── Defaults (will be overwritten by _apply_theme_colors) ──
PRIMARY = "#1a73e8"
PRIMARY_HOVER = "#1557b0"
BG = "#f0f2f5"
SIDEBAR_BG = "#202124"
TEXT = "#202124"
TEXT_SEC = "#5f6368"
SUCCESS = "#22c55e"
SUCCESS_HOVER = "#16a34a"
DANGER = "#ef4444"
DANGER_HOVER = "#dc2626"
WARNING = "#f59e0b"
WARNING_HOVER = "#d97706"
SECONDARY = "#9ca3af"
SECONDARY_HOVER = "#6b7280"
CARD_BG = "#ffffff"
DIVIDER = "#e5e7eb"
ROW_BG = "#f9fafb"
DELETE_HOVER = "#fee2e2"
SIDEBAR_TEXT = "#e8eaed"
SIDEBAR_HOVER = "#3c4043"
SIDEBAR_DIVIDER = "#3c4043"
SIDEBAR_SUB = "#9aa0a6"
INFO_BG = "#f0f7ff"

STATUS_COLORS = {}
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

        self.pages = {}
        self.current_frame = None
        self.current_page_key = None
        self._page_classes = {}
        self.nav_buttons = {}

        # Load saved theme (default: blue_light)
        self.current_theme = self._load_theme()
        _apply_theme_colors(self.current_theme)
        self.configure(fg_color=BG)

        # Build UI
        self._build_sidebar()
        self._build_content()
        self._register_page_classes()
        self.show_page("dashboard")

    # ── Theme Management ──
    def _load_theme(self):
        db = SessionLocal()
        try:
            name = get_setting(db, "theme_name", "blue_light")
            if name in THEMES:
                return name
        except Exception:
            pass
        finally:
            db.close()
        return "blue_light"

    def apply_theme(self, theme_name):
        """Apply a new theme and rebuild the entire UI."""
        if theme_name == self.current_theme:
            return
        if theme_name not in THEMES:
            return

        log.info(f"Switching theme: {self.current_theme} -> {theme_name}")
        self.current_theme = theme_name

        # Save to DB
        db = SessionLocal()
        try:
            set_setting(db, "theme_name", theme_name)
        finally:
            db.close()

        # Apply colors to module globals
        _apply_theme_colors(theme_name)

        # Remember current page
        saved_key = self.current_page_key or "dashboard"

        # Destroy all cached pages
        for key in list(self.pages.keys()):
            try:
                self.pages[key].destroy()
            except Exception:
                pass
        self.pages.clear()
        self.current_frame = None

        # Destroy sidebar & content
        try:
            self.sidebar.destroy()
        except Exception:
            pass
        try:
            self.content.destroy()
        except Exception:
            pass

        # Rebuild with new colors
        self.configure(fg_color=BG)
        self._build_sidebar()
        self._build_content()
        self.show_page(saved_key)

    # ── Sidebar ──
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR_BG)

        # Bottom items first (so they stay at bottom)
        ctk.CTkLabel(self.sidebar, text="v1.0", font=("Segoe UI", 10),
                      text_color=SIDEBAR_SUB).pack(side="bottom", pady=8)
        ctk.CTkFrame(self.sidebar, height=1, fg_color=SIDEBAR_DIVIDER).pack(
            fill="x", padx=10, pady=5, side="bottom"
        )

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=20, padx=16)

        ctk.CTkLabel(logo_frame, text="🎮", font=("", 36), text_color="white").pack()
        ctk.CTkLabel(logo_frame, text="Marouf", font=("Segoe UI", 20, "bold"),
                      text_color="white").pack(pady=(4, 0))
        ctk.CTkLabel(logo_frame, text="PlayStation Cafe", font=("Segoe UI", 11),
                      text_color=SIDEBAR_SUB).pack()

        ctk.CTkFrame(self.sidebar, height=1, fg_color=SIDEBAR_DIVIDER).pack(
            fill="x", padx=10, pady=5
        )

        # Navigation
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
                fg_color="transparent", text_color=SIDEBAR_TEXT,
                anchor="w", height=42, corner_radius=10,
                hover_color=SIDEBAR_HOVER,
                command=lambda k=key: self.show_page(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

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
                      font=("Segoe UI", 13), text_color=TEXT_SEC).pack(
            side="right", padx=20, pady=10
        )

        self.page_title_label = ctk.CTkLabel(
            self.topbar, text="", font=("Segoe UI", 13), text_color=TEXT_SEC
        )
        self.page_title_label.pack(side="left", padx=20, pady=10)

        # Scrollable pages container
        self.pages_frame = ctk.CTkScrollableFrame(
            self.content, corner_radius=0, fg_color=BG
        )
        self.pages_frame.pack(fill="both", expand=True)

    # ── Page Registration (lazy) ──
    def _register_page_classes(self):
        page_modules = {
            "dashboard": ("ui.dashboard", "DashboardPage"),
            "stations": ("ui.stations_page", "StationsPage"),
            "sessions": ("ui.sessions_page", "SessionsPage"),
            "customers": ("ui.customers_page", "CustomersPage"),
            "billing": ("ui.billing_page", "BillingPage"),
            "inventory": ("ui.inventory_page", "InventoryPage"),
            "employees": ("ui.employees_page", "EmployeesPage"),
            "reports": ("ui.reports_page", "ReportsPage"),
            "tournaments": ("ui.tournaments_page", "TournamentsPage"),
            "reservations": ("ui.reservations_page", "ReservationsPage"),
            "settings": ("ui.settings_page", "SettingsPage"),
        }

        self._page_classes = {}
        for key, (mod_path, cls_name) in page_modules.items():
            try:
                mod = __import__(mod_path, fromlist=[cls_name])
                cls = getattr(mod, cls_name)
                self._page_classes[key] = cls
                log.info(f"Registered page '{key}' -> {cls_name}")
            except Exception as e:
                log.error(f"Failed to register page '{key}': {e}\n{traceback.format_exc()}")

    # ── Page Switching ──
    def show_page(self, key):
        log.info(f"show_page('{key}')")
        self.current_page_key = key

        # Hide current page
        if self.current_frame:
            self.current_frame.pack_forget()

        # Lazy create page
        if key not in self.pages:
            log.info(f"Creating page '{key}' (lazy)...")
            try:
                cls = self._page_classes[key]
                self.pages[key] = cls(self.pages_frame, self)
                log.info(f"Page '{key}' created OK")
            except Exception as e:
                log.error(f"Page '{key}' creation FAILED: {e}\n{traceback.format_exc()}")
                # Show error in the content area
                err_frame = ctk.CTkFrame(self.pages_frame, fg_color=CARD_BG, corner_radius=12)
                err_frame.pack(fill="x", padx=20, pady=20)
                ctk.CTkLabel(
                    err_frame, text="⚠️ خطأ في تحميل الصفحة",
                    font=("Segoe UI", 18, "bold"), text_color=DANGER, anchor="e"
                ).pack(fill="x", padx=20, pady=(20, 5))
                ctk.CTkLabel(
                    err_frame, text=str(e),
                    font=("Segoe UI", 13), text_color=TEXT_SEC, anchor="e",
                    wraplength=600
                ).pack(fill="x", padx=20, pady=(5, 20))
                self.current_frame = err_frame
                return

        # Show page
        self.current_frame = self.pages[key]
        self.current_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Update title
        titles = {
            "dashboard": "لوحة التحكم", "stations": "إدارة المحطات",
            "sessions": "إدارة الجلسات", "customers": "إدارة العملاء",
            "billing": "الفواتير والمدفوعات", "inventory": "إدارة المخزون",
            "employees": "إدارة الموظفين", "reports": "التقارير المالية",
            "tournaments": "إدارة البطولات", "reservations": "إدارة الحجوزات",
            "settings": "الإعدادات",
        }
        self.page_title_label.configure(text=titles.get(key, ""))

        # Refresh data
        try:
            self.pages[key].refresh()
            log.info(f"Page '{key}' refresh OK")
        except Exception as e:
            log.error(f"Page '{key}' refresh FAILED: {e}\n{traceback.format_exc()}")

        # Highlight nav button
        for k, btn in self.nav_buttons.items():
            btn.configure(fg_color=PRIMARY if k == key else "transparent")


# ════════════════════════════════════════════════════════════
#  BasePage
# ════════════════════════════════════════════════════════════
class BasePage(ctk.CTkFrame):
    """Base class for all pages."""

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
    log.info(f"Python: {sys.version}")
    log.info(f"Working dir: {os.getcwd()}")
    log.info(f"Project dir: {PROJECT_DIR}")

    # Check dependencies first
    missing = check_dependencies()
    if missing:
        msg = f"المكتبات التالية غير مثبتة:\n\n" + "\n".join(f"  • {m}" for m in missing)
        msg += "\n\nيرجى تشغيل install.bat أولاً لتثبيت المكتبات المطلوبة."
        log.error(f"Missing dependencies: {missing}")
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("خطأ - مكتبات مفقودة", msg)
            root.destroy()
        except Exception:
            print(msg, file=sys.stderr)
        sys.exit(1)

    # Initialize database
    try:
        init_db()
        log.info("Database initialized OK")
    except Exception as e:
        log.error(f"Database init FAILED: {e}\n{traceback.format_exc()}")
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("خطأ", f"فشل في تهيئة قاعدة البيانات:\n{e}")
            root.destroy()
        except Exception:
            print(f"Database init failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Start app
    try:
        app = App()
        log.info("App created, starting mainloop")
        app.mainloop()
    except Exception as e:
        log.critical(f"FATAL: {e}\n{traceback.format_exc()}")
        error_msg = f"حدث خطأ في تشغيل البرنامج:\n\n{e}\n\nتفاصيل:\n{traceback.format_exc()}"
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("خطأ", error_msg)
            root.destroy()
        except Exception:
            print(error_msg, file=sys.stderr)