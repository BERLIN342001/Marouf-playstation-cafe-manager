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


def main(page: ft.Page):
    init_db()

    page.title = "Marouf - PlayStation Cafe Manager"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 1280
    page.window.height = 800
    page.window.min_width = 1024
    page.window.min_height = 600
    page.bgcolor = AppColors.BG
    page.theme = ft.Theme(color_scheme_seed=AppColors.PRIMARY, font_family="Segoe UI")

    state = {"current_idx": 0, "current_page": None}

    def build_sidebar():
        buttons = []
        for i, (label, icon, _) in enumerate(NAV_ITEMS):
            is_active = i == state["current_idx"]
            btn = ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(icon, size=20, color=COLORS.WHITE),
                    ft.Text(label, size=13, color=COLORS.WHITE, weight=ft.FontWeight.W_500),
                ], spacing=12),
                on_click=lambda e, idx=i: navigate(idx),
                style=ft.ButtonStyle(
                    bgcolor=AppColors.PRIMARY if is_active else COLORS.TRANSPARENT,
                ),
            )
            buttons.append(btn)

        return ft.Container(
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
                    padding=20,
                ),
                ft.Divider(color="#3c4043"),
                ft.Container(height=8),
                ft.Column(controls=buttons, spacing=2, scroll=ft.ScrollMode.AUTO, expand=True),
                ft.Divider(color="#3c4043"),
                ft.Container(content=ft.Text("v1.0", size=11, color="#9aa0a6"), padding=10),
            ], spacing=0),
            width=220,
            bgcolor=AppColors.SIDEBAR_BG,
        )

    def navigate(index):
        state["current_idx"] = index
        page.clean()
        render(index)

    def render(index):
        page.clean()

        # Sidebar
        sidebar = build_sidebar()

        # Page content
        _, _, page_cls = NAV_ITEMS[index]
        page_instance = page_cls(page)
        page_instance.build()
        state["current_page"] = page_instance

        # Top bar
        top_bar = ft.Container(
            content=ft.Row([
                ft.Text("Marouf PlayStation Cafe Manager", size=14, color=AppColors.TEXT_SECONDARY),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=getattr(ICONS, "REFRESH", "refresh"),
                    icon_color=AppColors.TEXT_SECONDARY,
                    tooltip="تحديث",
                    on_click=lambda e: do_refresh(),
                ),
            ]),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            bgcolor=AppColors.CARD_BG,
            border=ft.border.only(bottom=ft.BorderSide(1, AppColors.BORDER)),
        )

        # Content area
        content_area = ft.Container(
            content=page_instance,
            expand=True,
            bgcolor=AppColors.BG,
            padding=0,
        )

        main_col = ft.Column([top_bar, content_area], spacing=0, expand=True)

        page.add(ft.Row([sidebar, main_col], spacing=0, expand=True))
        page.update()

        # Load data after render
        def load():
            try:
                page_instance.refresh()
                page.update()
            except Exception:
                pass
        page.run_task(delayed_load, load)

    def do_refresh():
        p = state.get("current_page")
        if p and hasattr(p, 'refresh'):
            try:
                p.refresh()
                page.update()
            except Exception:
                pass

    async def delayed_load(fn):
        await asyncio.sleep(0.5)
        fn()

    async def auto_tick():
        while True:
            await asyncio.sleep(30)
            if state["current_idx"] == 0:
                try:
                    do_refresh()
                except Exception:
                    pass

    render(0)
    page.run_task(auto_tick)


if __name__ == "__main__":
    ft.app(target=main)