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


ICONS = ft.Icons if hasattr(ft, "Icons") else ft.icons
COLORS = ft.Colors if hasattr(ft, "Colors") else ft.colors
CONTROL_STATE = ft.ControlState if hasattr(ft, "ControlState") else ft.MaterialState


class NavigationItem:
    def __init__(self, icon, label, page_class):
        self.icon = icon
        self.label = label
        self.page_class = page_class


class MainApp(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.spacing = 0
        self.current_page = None
        self._initialized = False
        self.nav_items = [
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
        self.nav_buttons = []
        self.content_area = ft.Container(expand=True, content=ft.Container())
        self.build_navigation()

    def init_first_page(self):
        if not self._initialized:
            self._initialized = True
            self.navigate_to(0)

    def build_navigation(self):
        nav_buttons = []
        for i, item in enumerate(self.nav_items):
            btn = ft.ElevatedButton(
                content=ft.Row(
                    controls=[
                        ft.Icon(item.icon, size=20, color=COLORS.WHITE),
                        ft.Text(item.label, size=13, color=COLORS.WHITE,
                                weight=ft.FontWeight.W_500),
                    ],
                    spacing=12,
                ),
                on_click=lambda e, idx=i: self.navigate_to(idx),
                style=ft.ButtonStyle(
                    bgcolor={
                        CONTROL_STATE.DEFAULT: COLORS.TRANSPARENT,
                        CONTROL_STATE.HOVERED: "#3c4043",
                    },
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
            )
            nav_buttons.append(btn)
        self.nav_buttons = nav_buttons

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
        nav_item = self.nav_items[index]
        page_instance = nav_item.page_class(self.page)
        page_instance.build()
        self.current_page = page_instance

        # Update content
        self.content_area.content = ft.Container(
            content=page_instance,
            expand=True,
        )
        self.update()

        # Refresh data AFTER the control is in the tree
        def do_refresh():
            if hasattr(page_instance, 'refresh'):
                try:
                    page_instance.refresh()
                except Exception:
                    pass

        self.page.run_task(async_refresh, do_refresh)


async def async_refresh(refresh_fn):
    await asyncio.sleep(0.3)
    refresh_fn()


def main(page: ft.Page):
    # Initialize database
    init_db()

    # Page settings
    page.title = "Marouf - PlayStation Cafe Manager"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.rtl = True
    page.window.width = 1280
    page.window.height = 800
    page.window.min_width = 1024
    page.window.min_height = 600
    page.bgcolor = AppColors.BG

    # Custom theme
    page.theme = ft.Theme(
        color_scheme_seed=AppColors.PRIMARY,
        font_family="Segoe UI",
    )

    # Build layout
    app = MainApp(page)

    # Sidebar
    sidebar = ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                content=ft.Icon(ICONS.SPORTS_ESPORTS, size=36,
                                                color=COLORS.WHITE),
                                width=50, height=50,
                                bgcolor=AppColors.PRIMARY,
                                border_radius=14,
                                alignment=ft.alignment.center,
                            ),
                            ft.Text("Marouf", size=20, weight=ft.FontWeight.BOLD,
                                    color=COLORS.WHITE),
                            ft.Text("PlayStation Cafe", size=11,
                                    color="#9aa0a6"),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                    ),
                    padding=ft.padding.only(top=20, bottom=20, left=16, right=16),
                ),
                ft.Divider(color="#3c4043"),
                ft.Container(height=8),
                ft.Column(
                    controls=app.nav_buttons,
                    spacing=2,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                ft.Divider(color="#3c4043"),
                ft.Container(
                    content=ft.Text("v1.0", size=11, color="#9aa0a6",
                                    text_align=ft.TextAlign.CENTER),
                    padding=10,
                ),
            ],
            spacing=0,
        ),
        width=220,
        bgcolor=AppColors.SIDEBAR_BG,
    )

    # Main content
    def refresh_current():
        if app.current_page and hasattr(app.current_page, 'refresh'):
            try:
                app.current_page.refresh()
            except Exception:
                pass

    main_content = ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text("Marouf PlayStation Cafe Manager",
                                    size=14, color=AppColors.TEXT_SECONDARY),
                            ft.Container(expand=True),
                            ft.IconButton(icon=ICONS.REFRESH, icon_color=AppColors.TEXT_SECONDARY,
                                          tooltip="تحديث",
                                          on_click=lambda e: refresh_current()),
                        ],
                    ),
                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    bgcolor=AppColors.CARD_BG,
                    border=ft.border.only(bottom=ft.BorderSide(1, AppColors.BORDER)),
                ),
                app.content_area,
            ],
            spacing=0,
            expand=True,
        ),
        expand=True,
        bgcolor=AppColors.BG,
    )

    # Layout
    layout = ft.Row(
        controls=[sidebar, main_content],
        spacing=0,
        expand=True,
    )

    page.add(layout)
    page.update()

    # Initialize first page AFTER layout is in the tree
    app.init_first_page()

    # Timer for auto-refresh
    async def run_timer():
        while True:
            await asyncio.sleep(30)
            if app.current_page and isinstance(app.current_page, DashboardPage):
                try:
                    app.current_page.refresh()
                except Exception:
                    pass

    page.run_task(run_timer)


if __name__ == "__main__":
    ft.app(target=main)