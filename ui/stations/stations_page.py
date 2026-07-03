import flet as ft
from database.db import SessionLocal
from database.models import StationStatus
from services.services import (
    create_station, get_stations, get_station_by_id,
    update_station, delete_station, get_station_stats
)
from ui.components.widgets import (
    AppColors, PageTemplate, show_snackbar, make_search_field,
    make_confirm_dialog, make_status_chip, make_form_field,
    make_text_field, make_dropdown, format_currency
)


class StationsPage(PageTemplate):
    def __init__(self, page):
        super().__init__(page, "إدارة المحطات")
        self.search_text = ""
        self.filter_status = None

    def build_content(self):
        self.stations_grid = ft.Row(wrap=True, spacing=12, run_spacing=12)
        self.stats_row = ft.Row(spacing=12)
        return self.build_body()

    def build_body(self):
        return ft.Column(
            controls=[
                # Stats
                self.stats_row,
                ft.Container(height=10),
                # Search & Filter
                ft.Row(
                    controls=[
                        make_search_field(
                            on_change=self.on_search,
                            placeholder="ابحث عن محطة..."
                        ),
                        ft.Dropdown(
                            width=180,
                            hint_text="الحالة",
                            options=[
                                ft.dropdown.Option(key="", text="الكل"),
                                ft.dropdown.Option(key="available", text="فارغة"),
                                ft.dropdown.Option(key="occupied", text="مشغولة"),
                                ft.dropdown.Option(key="maintenance", text="صيانة"),
                            ],
                            on_change=self.on_filter,
                            border_radius=10,
                            filled=True,
                        ),
                    ],
                    spacing=12,
                ),
                ft.Container(height=10),
                self.stations_grid,
            ],
            spacing=0,
            expand=True,
        )

    def on_search(self, e):
        self.search_text = e.control.value
        self.refresh()

    def on_filter(self, e):
        self.filter_status = e.control.value if e.control.value else None
        self.refresh()

    def refresh(self):
        db = SessionLocal()
        try:
            stats = get_station_stats(db)
            self.stats_row.controls = [
                ft.Container(
                    content=ft.Row([
                        ft.Container(width=12, height=12, bgcolor=AppColors.STATION_AVAILABLE, border_radius=3),
                        ft.Text(f"فارغة: {stats['available']}", size=13, color=AppColors.TEXT),
                    ], spacing=6),
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Container(width=12, height=12, bgcolor=AppColors.STATION_OCCUPIED, border_radius=3),
                        ft.Text(f"مشغولة: {stats['occupied']}", size=13, color=AppColors.TEXT),
                    ], spacing=6),
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Container(width=12, height=12, bgcolor=AppColors.STATION_MAINTENANCE, border_radius=3),
                        ft.Text(f"صيانة: {stats['maintenance']}", size=13, color=AppColors.TEXT),
                    ], spacing=6),
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Container(width=12, height=12, bgcolor=AppColors.STATION_RESERVED, border_radius=3),
                        ft.Text(f"محجوزة: {stats['reserved']}", size=13, color=AppColors.TEXT),
                    ], spacing=6),
                ),
            ]

            stations = get_stations(db, status=self.filter_status)
            if self.search_text:
                stations = [s for s in stations if self.search_text.lower() in s.name.lower()]

            cards = []
            for st in stations:
                status_color = {
                    "available": AppColors.STATION_AVAILABLE,
                    "occupied": AppColors.STATION_OCCUPIED,
                    "maintenance": AppColors.STATION_MAINTENANCE,
                    "reserved": AppColors.STATION_RESERVED,
                }.get(st.status, AppColors.TEXT_SECONDARY)

                cards.append(
                    ft.Card(
                        elevation=2,
                        width=200,
                        content=ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Row([
                                        ft.Text(st.name, size=16, weight=ft.FontWeight.BOLD,
                                                color=AppColors.TEXT),
                                        ft.Icon(ft.icons.MORE_VERT, size=20,
                                                on_click=lambda e, sid=st.id: self.show_station_menu(e, sid)),
                                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                    ft.Text(st.console_type, size=13, color=AppColors.TEXT_SECONDARY),
                                    ft.Container(height=8),
                                    ft.Row([
                                        ft.Container(width=10, height=10, bgcolor=status_color, border_radius=5),
                                        ft.Text(st.status, size=12, color=status_color),
                                    ], spacing=6),
                                    ft.Container(height=4),
                                    ft.Text(f"سعر الساعة: {format_currency(st.hourly_rate)}", size=13,
                                            color=AppColors.TEXT),
                                    ft.Text(f"كنترولر: {st.controller_count}", size=12,
                                            color=AppColors.TEXT_SECONDARY),
                                    ft.Row([
                                        ft.Icon(ft.icons.VRPA_DESKTOP if st.has_vr else ft.icons.VRPA_DESKTOP_OUTLINED,
                                                size=16, color=AppColors.PRIMARY if st.has_vr else AppColors.TEXT_SECONDARY),
                                        ft.Icon(ft.icons.SPORTS_SCOREBOARD if st.has_wheel else ft.icons.SPORTS_SCOREBOARD_OUTLINED,
                                                size=16, color=AppColors.PRIMARY if st.has_wheel else AppColors.TEXT_SECONDARY),
                                    ], spacing=8),
                                ],
                                spacing=4,
                            ),
                            padding=15,
                            on_click=lambda e, sid=st.id: self.show_station_menu(e, sid),
                        ),
                    )
                )

            self.stations_grid.controls = cards if cards else [
                ft.Container(
                    content=ft.Text("لا توجد محطات", size=15, color=AppColors.TEXT_SECONDARY,
                                    ),
                    alignment=ft.alignment.center,
                    padding=40, expand=True,
                )
            ]
            self.update()
        finally:
            db.close()

    def show_station_menu(self, e, station_id):
        db = SessionLocal()
        try:
            station = get_station_by_id(db, station_id)
            if not station:
                return

            status_options = {
                "available": "فارغة", "occupied": "مشغولة",
                "maintenance": "صيانة", "reserved": "محجوزة",
            }

            def change_status(status):
                def handler(e):
                    update_station(db, station_id, status=status)
                    dlg.open = False
                    self.page.update()
                    self.refresh()
                    show_snackbar(self.page, "تم تحديث حالة المحطة", AppColors.SUCCESS)
                return handler

            items = []
            for skey, slabel in status_options.items():
                items.append(ft.PopupMenuItem(
                    text=slabel,
                    on_click=change_status(skey),
                ))
            items.append(ft.PopupMenuItem())
            items.append(ft.PopupMenuItem(
                text="تعديل", on_click=lambda e: self.show_edit_dialog(station_id)))
            items.append(ft.PopupMenuItem(
                text="حذف",
                on_click=lambda e: self.confirm_delete(station_id)))

            ft.PopupMenu(
                items=items,
            ).open = True
        finally:
            db.close()

    def show_add_dialog(self):
        self._show_form_dialog(None)

    def show_edit_dialog(self, station_id):
        db = SessionLocal()
        try:
            station = get_station_by_id(db, station_id)
            if station:
                self._show_form_dialog(station)
        finally:
            db.close()

    def _show_form_dialog(self, station):
        is_edit = station is not None
        name_field = make_text_field("اسم المحطة", station.name if is_edit else "")
        console_field = make_dropdown(
            "نوع الكونسول",
            [("PS5", "PS5"), ("PS4", "PS4"), ("PS3", "PS3")],
            station.console_type if is_edit else "PS5"
        )
        rate_field = make_text_field("سعر الساعة", station.hourly_rate if is_edit else "30")
        controllers_field = make_text_field("عدد الكنترولرز", station.controller_count if is_edit else "2")
        vr_field = ft.Switch(label="VR", value=station.has_vr if is_edit else False)
        wheel_field = ft.Switch(label="دركسون", value=station.has_wheel if is_edit else False)

        def save(e):
            db = SessionLocal()
            try:
                if is_edit:
                    update_station(db, station.id,
                                   name=name_field.value,
                                   console_type=console_field.value,
                                   hourly_rate=float(rate_field.value or 30),
                                   controller_count=int(controllers_field.value or 2),
                                   has_vr=vr_field.value,
                                   has_wheel=wheel_field.value)
                else:
                    create_station(db,
                                   name=name_field.value,
                                   console_type=console_field.value,
                                   hourly_rate=float(rate_field.value or 30),
                                   controller_count=int(controllers_field.value or 2),
                                   has_vr=vr_field.value,
                                   has_wheel=wheel_field.value)
                dlg.open = False
                self.page.update()
                self.refresh()
                show_snackbar(self.page, "تم حفظ المحطة بنجاح", AppColors.SUCCESS)
            except Exception as ex:
                show_snackbar(self.page, str(ex), AppColors.DANGER)
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("تعديل محطة" if is_edit else "إضافة محطة جديدة",
                          ),
            content=ft.Column(
                controls=[name_field, console_field, rate_field, controllers_field,
                          ft.Row([vr_field, wheel_field], spacing=20)],
                spacing=12, width=400,
            ),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda e: close(e)),
                ft.ElevatedButton("حفظ", on_click=save,
                                  style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def close(e):
            dlg.open = False
            self.page.update()

        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def confirm_delete(self, station_id):
        dlg = make_confirm_dialog(
            "حذف المحطة",
            "هل أنت متأكد من حذف هذه المحطة؟",
            lambda: self._do_delete(station_id),
            self.page
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _do_delete(self, station_id):
        db = SessionLocal()
        try:
            delete_station(db, station_id)
            self.refresh()
            show_snackbar(self.page, "تم حذف المحطة", AppColors.DANGER)
        finally:
            db.close()