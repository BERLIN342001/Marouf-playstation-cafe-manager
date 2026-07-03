import flet as ft
from utils.helpers import (
    get_status_color, get_status_label, get_payment_label,
    get_role_label, get_shift_label, format_currency,
    format_datetime, format_duration, get_active_session_duration_minutes
)

# ════════════════════════════════════════════════════════════
#  THEME / COLORS
# ════════════════════════════════════════════════════════════
class AppColors:
    PRIMARY = "#1a73e8"
    PRIMARY_DARK = "#1557b0"
    SECONDARY = "#5f6368"
    BG = "#f8f9fa"
    CARD_BG = "#ffffff"
    SIDEBAR_BG = "#202124"
    SIDEBAR_TEXT = "#e8eaed"
    SIDEBAR_ACTIVE = "#1a73e8"
    TEXT = "#202124"
    TEXT_SECONDARY = "#5f6368"
    SUCCESS = "#22c55e"
    DANGER = "#ef4444"
    WARNING = "#f59e0b"
    INFO = "#3b82f6"
    BORDER = "#dadce0"
    STATION_AVAILABLE = "#22c55e"
    STATION_OCCUPIED = "#ef4444"
    STATION_MAINTENANCE = "#f59e0b"
    STATION_RESERVED = "#3b82f6"


# ════════════════════════════════════════════════════════════
#  COMMON WIDGETS
# ════════════════════════════════════════════════════════════
class StatCard(ft.Card):
    def __init__(self, title: str, value: str, icon: str, color: str = AppColors.PRIMARY):
        super().__init__()
        self.elevation = 2
        self.margin = ft.margin.only(bottom=10)
        self.content = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(icon, size=30, color=ft.colors.WHITE),
                        width=56, height=56,
                        bgcolor=color,
                        border_radius=12,
                        alignment=ft.alignment.center,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(value, size=22, weight=ft.FontWeight.BOLD,
                                    color=AppColors.TEXT),
                            ft.Text(title, size=13, color=AppColors.TEXT_SECONDARY),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=15,
            ),
            padding=20,
        )


def make_search_field(on_change=None, placeholder: str = "بحث..."):
    return ft.TextField(
        hint_text=placeholder,
        prefix_icon=ft.icons.SEARCH,
        on_change=on_change,
        border_radius=10,
        filled=True,
        focused_border_color=AppColors.PRIMARY,
        text_direction=ft.TextDirection.RTL,
        expand=True,
    )


def make_elevated_button(text: str, on_click=None, icon=None, color=None, style=ft.ButtonStyle.FILLED):
    return ft.ElevatedButton(
        text=text,
        on_click=on_click,
        icon=icon,
        style=ft.ButtonStyle(
            bgcolor=ft.colors.TRANSPARENT,
            color=color or AppColors.PRIMARY,
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(weight=ft.FontWeight.W_600),
        ) if style == ft.ButtonStyle.FILLED else ft.ButtonStyle(
            bgcolor=ft.colors.TRANSPARENT,
            color=color or AppColors.PRIMARY,
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(weight=ft.FontWeight.W_600),
        ),
    )


def make_fab(icon, on_click, tooltip=""):
    return ft.FloatingActionButton(
        icon=icon,
        on_click=on_click,
        bgcolor=AppColors.PRIMARY,
        tooltip=tooltip,
    )


def show_snackbar(page, message: str, color: str = AppColors.PRIMARY):
    snack = ft.SnackBar(
        content=ft.Text(message, color=ft.colors.WHITE, text_direction=ft.TextDirection.RTL),
        bgcolor=color,
    )
    page.overlay.append(snack)
    snack.open = True
    page.update()


def make_status_chip(status: str):
    color = get_status_color(status)
    label = get_status_label(status)
    return ft.Container(
        content=ft.Text(label, size=11, color=ft.colors.WHITE, weight=ft.FontWeight.W_600),
        bgcolor=color,
        padding=ft.padding.symmetric(horizontal=12, vertical=4),
        border_radius=20,
    )


def make_confirm_dialog(title: str, message: str, on_confirm, page_ref):
    def confirm(e):
        dlg.open = False
        page_ref.update()
        on_confirm()

    def cancel(e):
        dlg.open = False
        page_ref.update()

    dlg = ft.AlertDialog(
        title=ft.Text(title, text_direction=ft.TextDirection.RTL),
        content=ft.Text(message, text_direction=ft.TextDirection.RTL),
        actions=[
            ft.TextButton("إلغاء", on_click=cancel),
            ft.ElevatedButton("تأكيد", on_click=confirm,
                              style=ft.ButtonStyle(bgcolor=AppColors.DANGER)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    return dlg


def make_form_field(label: str, field_widget, expand=False):
    return ft.Column(
        controls=[
            ft.Text(label, size=13, weight=ft.FontWeight.W_600,
                    color=AppColors.TEXT_SECONDARY, text_direction=ft.TextDirection.RTL),
            field_widget,
        ],
        spacing=4,
        expand=expand,
    )


def make_text_field(label: str, value="", expand=False, text_direction=ft.TextDirection.RTL, **kwargs):
    field = ft.TextField(
        value=str(value) if value else "",
        border_radius=10,
        filled=True,
        text_direction=text_direction,
        label=label,
        expand=expand,
        **kwargs
    )
    return field


def make_dropdown(label: str, options: list, value=None, expand=False):
    dd = ft.Dropdown(
        label=label,
        options=[ft.dropdown.Option(key=o[0], text=o[1]) for o in options],
        value=value,
        border_radius=10,
        filled=True,
        expand=expand,
    )
    return dd


def make_section_header(title: str, action_widget=None):
    return ft.Row(
        controls=[
            ft.Text(title, size=18, weight=ft.FontWeight.BOLD,
                    color=AppColors.TEXT, text_direction=ft.TextDirection.RTL),
            ft.Container(expand=True),
            action_widget or ft.Container(),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )


class PageTemplate(ft.Column):
    """Base template for all pages with header and content area."""
    def __init__(self, page, title: str):
        super().__init__()
        self.page = page
        self.title = title
        self.spacing = 0
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO

    def build(self):
        self.controls = [
            ft.Container(
                content=ft.Text(self.title, size=24, weight=ft.FontWeight.BOLD,
                                color=AppColors.TEXT),
                padding=ft.padding.only(left=20, right=20, top=15, bottom=10),
            ),
            ft.Divider(height=1, color=AppColors.BORDER),
            ft.Container(
                content=self.build_content(),
                padding=20,
                expand=True,
            ),
        ]
        return self

    def build_content(self) -> ft.Control:
        return ft.Text("Page content")