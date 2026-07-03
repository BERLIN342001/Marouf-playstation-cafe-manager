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


class NavigationItem:
    def __init__(self, icon, label, page_class):
        self.icon = icon
        self.label = label
        self.page_class = page_class


NAV_ITEMS = [
    NavigationItem(ICONS.DASHBOARD, "لوحة التحكم", DashboardPage),
    NavigationItem(ICONS.SPORTS_ESPORTS, "المحطات", StationsPage),
    NavigationItem(ICONS.PLAY_CIRCLE, "الجلسات", SessionsPage),
    NavigationItem(ICONS.PEOPLE, "العملاء", CustomersPage),
    NavigationItem(ICONS.RECEIPT_LONG, "الفواتير", BillingPage),
    NavigationItem(ICONS.INVENTORY_2, "المخزون", InventoryPage),
    NavigationItem(ICONS.BADGE, "الموظفين", EmployeesPage),
    NavigationItem(ICONS.BAR_CHART, "التقارير", ReportsPage),
    NavigationItem(ICONS.EMOJI_EVENTS, "البطولات", TournamentsPage),
    NavigationItem(ICONS.EVENT, "الحجوزات", ReservationsPage),
    NavigationItem(ICONS.SETTINGS, "الإعدادات", SettingsPage),
]


class CafeManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_page = None
        self.nav_buttons = []
        self.content_container = ft.Container(expand=True)
        self._build_sidebar()
        self._build_layout()

    def _build_sidebar(self):
        nav_btns = []
        for i, item in enumerate(NAV_ITEMS):
            btn = ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(item.icon, size=20, color=COLORS.WHITE),
                    ft.Text(item.label, size=13, color=COLORS.WHITE, weight=ft.FontWeight.W_500),
                ], spacing=12),
                on_click=lambda e, idx=i: self.navigate_to(idx),
                style=ft.ButtonStyle(
                    bgcolor=COLORS.TRANSPARENT,
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
            )
            nav_btns.append(btn)
        self.nav_buttons = nav_btns

        self.sidebar = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Icon(ICONS.SPORTS_ESPORTS, size=36, color=COLORS.WHITE),
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
                ft.Container(
                    content=ft.Text("v1.0", size=11, color="#9aa0a6", text_align=ft.TextAlign.CENTER),
                    padding=10,
                ),
            ], spacing=0),
            width=220,
            bgcolor=AppColors.SIDEBAR_BG,
        )

    def _build_layout(self):
        self.top_bar = ft.Container(
            content=ft.Row([
                ft.Text("Marouf PlayStation Cafe Manager", size=14, color=AppColors.TEXT_SECONDARY),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ICONS.REFRESH, icon_color=AppColors.TEXT_SECONDARY,
                    tooltip="تحديث", on_click=self._on_refresh,
                ),
            ]),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            bgcolor=AppColors.CARD_BG,
            border=ft.border.only(bottom=ft.BorderSide(1, AppColors.BORDER)),
        )

        self.main_column = ft.Column([
            self.top_bar,
            self.content_container,
        ], spacing=0, expand=True)

        self.main_container = ft.Container(
            content=self.main_column,
            expand=True,
            bgcolor=AppColors.BG,
        )

        self.layout = ft.Row([self.sidebar, self.main_container], spacing=0, expand=True)

    def _on_refresh(self, e=None):
        if self.current_page and hasattr(self.current_page, 'refresh'):
            try:
                self.current_page.refresh()
            except Exception:
                pass
            self.page.update()

    def navigate_to(self, index):
        # Update nav button styles
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.style = ft.ButtonStyle(
                    bgcolor=AppColors.PRIMARY,
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    shape=ft.RoundedRectangleBorder(radius=10),
                )
            else:
                btn.style = ft.ButtonStyle(
                    bgcolor=COLORS.TRANSPARENT,
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    shape=ft.RoundedRectangleBorder(radius=10),
                )

        # Build the page
        item = NAV_ITEMS[index]
        page_instance = item.page_class(self.page)
        page_instance.build()
        self.current_page = page_instance

        # Swap content
        self.content_container.content = page_instance
        self.page.update()

        # Refresh data after render
        def do_refresh():
            if hasattr(page_instance, 'refresh'):
                try:
                    page_instance.refresh()
                    self.page.update()
                except Exception:
                    pass

        self.page.run_task(self._delayed_refresh, do_refresh)

    @staticmethod
    async def _delayed_refresh(fn):
        await asyncio.sleep(0.5)
        fn()

    async def auto_refresh(self):
        while True:
            await asyncio.sleep(30)
            if self.current_page and isinstance(self.current_page, DashboardPage):
                try:
                    self.current_page.refresh()
                    self.page.update()
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

    app = CafeManager(page)
    page.add(app.layout)
    page.update()
    app.navigate_to(0)
    page.run_task(app.auto_refresh)


if __name__ == "__main__":
    ft.app(target=main)