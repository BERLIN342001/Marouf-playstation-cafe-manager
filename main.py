import asyncio
import flet as ft
from database.db import init_db
from ui.components.widgets import AppColors
from ui.dashboard import DashboardPage
from ui.stations.stations_page import StationsPage
from ui.sessions.sessions_page import SessionsPage
from ui.customers.customers_page import CustomersPage
from ui.billing.billing_page import BillingPage
from ui.inventory.inventory_page import InventoryPage
from ui.employees.employees_page import EmployeesPage
from ui.reports.reports_page import ReportsPage
from ui.tournaments.tournaments_page import TournamentsPage
from ui.reservations.reservations_page import ReservationsPage
from ui.settings.settings_page import SettingsPage

ICONS = getattr(ft, "Icons", ft.icons)
COLORS = getattr(ft, "Colors", ft.colors)


NAV_ITEMS = [
    ("لوحة التحكم", getattr(ICONS, "DASHBOARD", "dashboard"), DashboardPage),
    ("المحطات", getattr(ICONS, "SPORTS_ESPORTS", "sports_esports"), StationsPage),
    ("الجلسات", getattr(ICONS, "PLAY_CIRCLE", "play_circle"), SessionsPage),
    ("العملاء", getattr(ICONS, "PEOPLE", "people"), CustomersPage),
    ("الفواتير", getattr(ICONS, "RECEIPT_LONG", "receipt_long"), BillingPage),
    ("المخزون", getattr(ICONS, "INVENTORY_2", "inventory_2"), InventoryPage),
    ("الموظفين", getattr(ICONS, "BADGE", "badge"), EmployeesPage),
    ("التقارير", getattr(ICONS, "BAR_CHART", "bar_chart"), ReportsPage),
    ("البطولات", getattr(ICONS, "EMOJI_EVENTS", "emoji_events"), TournamentsPage),
    ("الحجوزات", getattr(ICONS, "EVENT", "event"), ReservationsPage),
    ("الإعدادات", getattr(ICONS, "SETTINGS", "settings"), SettingsPage),
]


class App:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_page_instance = None
        self.nav_buttons = []
        self.content_column = ft.Column(spacing=0, expand=True)

        # Build sidebar
        self.nav_buttons = []
        for i, (label, icon, _) in enumerate(NAV_ITEMS):
            btn = ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(icon, size=20, color=COLORS.WHITE),
                    ft.Text(label, size=13, color=COLORS.WHITE, weight=ft.FontWeight.W_500),
                ], spacing=12),
                on_click=lambda e, idx=i: self.go(idx),
            )
            self.nav_buttons.append(btn)

        sidebar = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Icon(NAV_ITEMS[1][1], size=36, color=COLORS.WHITE),
                            width=50, height=50,
                            bgcolor=AppColors.PRIMARY,
                            border_radius=14,
                            alignment=ft.alignment.center,
                        ),
                        ft.Text("Marouf", size=20, weight=ft.FontWeight.BOLD, color=COLORS.WHITE),
                        ft.Text("PlayStation Cafe", size=11, color="#9aa0a6"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    padding=ft.padding.only(top=20, bottom=20, left=16, right=16),
                ),
                ft.Divider(color="#3c4043"),
                ft.Container(height=8),
                ft.Column(controls=self.nav_buttons, spacing=2, scroll=ft.ScrollMode.AUTO, expand=True),
                ft.Divider(color="#3c4043"),
                ft.Container(content=ft.Text("v1.0", size=11, color="#9aa0a6"), padding=10),
            ], spacing=0),
            width=220,
            bgcolor=AppColors.SIDEBAR_BG,
        )

        # Top bar
        top_bar = ft.Container(
            content=ft.Row([
                ft.Text("Marouf PlayStation Cafe Manager", size=14, color=AppColors.TEXT_SECONDARY),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=getattr(ICONS, "REFRESH", "refresh"),
                    icon_color=AppColors.TEXT_SECONDARY,
                    tooltip="تحديث",
                    on_click=lambda e: self._refresh(),
                ),
            ]),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            bgcolor=AppColors.CARD_BG,
            border=ft.border.only(bottom=ft.BorderSide(1, AppColors.BORDER)),
        )

        # Main layout
        self.main_col = ft.Column([top_bar, self.content_column], spacing=0, expand=True)
        main_area = ft.Container(content=self.main_col, expand=True, bgcolor=AppColors.BG)

        self.layout = ft.Row([sidebar, main_area], spacing=0, expand=True)

    def go(self, index):
        # Highlight active button
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.style = ft.ButtonStyle(bgcolor=AppColors.PRIMARY)
            else:
                btn.style = ft.ButtonStyle(bgcolor=COLORS.TRANSPARENT)
            btn.update()

        # Build page
        _, _, page_cls = NAV_ITEMS[index]
        self.current_page_instance = page_cls(self.page)
        self.current_page_instance.build()

        # Replace content
        self.content_column.controls.clear()
        self.content_column.controls.append(self.current_page_instance)
        self.page.update()

        # Load data
        def load():
            try:
                self.current_page_instance.refresh()
                self.page.update()
            except Exception:
                pass
        self.page.run_task(self._delayed, load)

    def _refresh(self):
        if self.current_page_instance and hasattr(self.current_page_instance, 'refresh'):
            try:
                self.current_page_instance.refresh()
                self.page.update()
            except Exception:
                pass

    @staticmethod
    async def _delayed(fn):
        await asyncio.sleep(0.3)
        fn()

    async def auto_refresh(self):
        while True:
            await asyncio.sleep(30)
            try:
                self._refresh()
            except Exception:
                pass


def main(page: ft.Page):
    init_db()

    page.title = "Marouf - PlayStation Cafe Manager"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.rtl = True
    page.window.width = 1280
    page.window.height = 800
    page.window.min_width = 1024
    page.window.min_height = 600
    page.bgcolor = AppColors.BG
    page.theme = ft.Theme(color_scheme_seed=AppColors.PRIMARY, font_family="Segoe UI")

    app = App(page)
    page.add(app.layout)
    app.go(0)
    page.run_task(app.auto_refresh)


if __name__ == "__main__":
    ft.app(target=main)