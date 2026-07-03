import flet as ft
from datetime import datetime
from database.db import SessionLocal
from services.services import (
    start_session, end_session, cancel_session,
    get_sessions, get_active_sessions, get_session_by_id,
    get_stations, get_customers, get_packages, process_session_payment
)
from ui.components.widgets import (
    AppColors, PageTemplate, show_snackbar, make_status_chip,
    make_form_field, make_text_field, make_dropdown,
    format_currency, format_datetime, format_duration,
    get_status_label, get_status_color, make_confirm_dialog
)


class SessionsPage(PageTemplate):
    def __init__(self, page):
        super().__init__(page, "إدارة الجلسات")
        self.tab_active = True

    def build_content(self):
        self.tabs = ft.Tabs(
            selected_index=0,
            on_change=self.on_tab_change,
            tabs=[
                ft.Tab(text="الجلسات النشطة", icon=ft.icons.PLAY_CIRCLE),
                ft.Tab(text="سجل الجلسات", icon=ft.icons.HISTORY),
            ],
            animation_duration=200,
        )
        self.active_list = ft.Column(spacing=8)
        self.history_list = ft.Column(spacing=8)
        self.end_btn_row = ft.Row(spacing=10)
        return ft.Column(controls=[self.tabs, ft.Container(height=15),
                                   self.end_btn_row, self.active_list, self.history_list],
                         spacing=0, expand=True)

    def on_tab_change(self, e):
        self.tab_active = e.control.selected_index == 0
        self.refresh()

    def refresh(self):
        db = SessionLocal()
        try:
            if self.tab_active:
                self.refresh_active(db)
            else:
                self.refresh_history(db)
            self.update()
        finally:
            db.close()

    def refresh_active(self, db):
        active = get_active_sessions(db)
        stations = get_stations(db)
        self.end_btn_row.controls = [
            ft.ElevatedButton(
                "بدء جلسة جديدة", icon=ft.icons.ADD,
                on_click=lambda e: self.show_start_dialog(),
                style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY,
                                     shape=ft.RoundedRectangleBorder(radius=10)),
            ),
        ]

        if not active:
            self.active_list.controls = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.PLAY_CIRCLE_OUTLINE, size=48, color=AppColors.TEXT_SECONDARY),
                        ft.Text("لا توجد جلسات نشطة", size=15,
                                color=AppColors.TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER),
                    padding=40, alignment=ft.alignment.center, expand=True)
            ]
            return

        items = []
        for s in active:
            dur = 0
            if s.start_time:
                dur = int((datetime.now() - s.start_time).total_seconds() / 60)

            station = s.station
            customer = s.customer
            cust_name = customer.name if customer else "زائر"
            st_name = station.name if station else f"محطة {s.station_id}"

            cost = 0
            if station and station.hourly_rate:
                cost = round((dur / 60) * station.hourly_rate, 2)

            items.append(
                ft.Card(elevation=1, margin=ft.margin.only(bottom=8),
                    content=ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Text(st_name, size=11, color=ft.colors.WHITE,
                                                weight=ft.FontWeight.BOLD),
                                width=60, height=60, bgcolor=AppColors.DANGER,
                                border_radius=12, alignment=ft.alignment.center,
                            ),
                            ft.Column([
                                ft.Text(cust_name, size=15, weight=ft.FontWeight.W_600,
                                        color=AppColors.TEXT),
                                ft.Text(f"المدة: {format_duration(dur)} | التكلفة: {format_currency(cost)}",
                                        size=12, color=AppColors.TEXT_SECONDARY),
                                ft.Text(f"بدأت: {format_datetime(s.start_time)}", size=11,
                                        color=AppColors.TEXT_SECONDARY),
                            ], spacing=2, expand=True),
                            ft.Column([
                                ft.ElevatedButton("إنهاء", icon=ft.icons.STOP,
                                    on_click=lambda e, sid=s.id: self.end_session_action(sid),
                                    style=ft.ButtonStyle(bgcolor=AppColors.DANGER,
                                                         shape=ft.RoundedRectangleBorder(radius=8))),
                                ft.TextButton("إلغاء", on_click=lambda e, sid=s.id: self.cancel_session_action(sid)),
                            ], spacing=4),
                        ], spacing=12),
                        padding=15,
                    ))
            )
        self.active_list.controls = items

    def refresh_history(self, db):
        sessions = get_sessions(db, status="completed")
        self.end_btn_row.controls = []

        if not sessions:
            self.history_list.controls = [
                ft.Container(content=ft.Text("لا توجد جلسات سابقة", size=15,
                    color=AppColors.TEXT_SECONDARY),
                    padding=40, alignment=ft.alignment.center, expand=True)
            ]
            return

        items = []
        for s in sessions[:50]:
            customer = s.customer
            station = s.station
            cust_name = customer.name if customer else "زائر"
            st_name = station.name if station else f"محطة {s.station_id}"

            items.append(
                ft.Card(elevation=1, margin=ft.margin.only(bottom=6),
                    content=ft.Container(
                        content=ft.Row([
                            ft.Text(str(s.id), size=12, color=ft.colors.WHITE,
                                    weight=ft.FontWeight.BOLD),
                            ft.Column([
                                ft.Text(f"{cust_name} - {st_name}", size=14,
                                        weight=ft.FontWeight.W_500, color=AppColors.TEXT),
                                ft.Text(f"المدة: {format_duration(s.duration_minutes)} | {format_currency(s.total_cost)}",
                                        size=12, color=AppColors.TEXT_SECONDARY),
                            ], spacing=2, expand=True),
                            make_status_chip(s.status),
                            ft.Text(format_datetime(s.start_time), size=11,
                                    color=AppColors.TEXT_SECONDARY),
                        ], spacing=12),
                        padding=12))
            )
        self.history_list.controls = items

    def show_start_dialog(self):
        db = SessionLocal()
        try:
            stations = get_stations(db)
            customers = get_customers(db, active_only=True)
            packages = get_packages(db)

            available_stations = [s for s in stations if s.status == "available"]
            station_opts = [(str(s.id), f"{s.name} ({s.console_type})") for s in available_stations]
            customer_opts = [("0", "زائر")] + [(str(c.id), f"{c.name} - {c.phone}") for c in customers]
            package_opts = [("", "بدون باقة")] + [(str(p.id), f"{p.name} - {p.hours} ساعة - {p.price} ج.م") for p in packages]

            if not station_opts:
                show_snackbar(self.page, "لا توجد محطات متاحة!", AppColors.WARNING)
                return

            station_dd = make_dropdown("المحطة", station_opts, station_opts[0][0], expand=True)
            customer_dd = make_dropdown("العميل", customer_opts, "0", expand=True)
            package_dd = make_dropdown("الباقة", package_opts, "", expand=True)

            def save(e):
                try:
                    sid = int(station_dd.value)
                    cid = int(customer_dd.value) if customer_dd.value != "0" else None
                    pkg_id = int(package_dd.value) if package_dd.value else None
                    is_pkg = pkg_id is not None
                    start_session(db, station_id=sid, customer_id=cid,
                                  is_package=is_pkg, package_id=pkg_id)
                    dlg.open = False
                    self.page.update()
                    self.refresh()
                    show_snackbar(self.page, "تم بدء الجلسة بنجاح", AppColors.SUCCESS)
                except Exception as ex:
                    show_snackbar(self.page, str(ex), AppColors.DANGER)

            dlg = ft.AlertDialog(
                title=ft.Text("بدء جلسة جديدة"),
                content=ft.Column([station_dd, customer_dd, package_dd], spacing=12, width=450),
                actions=[
                    ft.TextButton("إلغاء", on_click=lambda e: close(e)),
                    ft.ElevatedButton("بدء", on_click=save,
                                      style=ft.ButtonStyle(bgcolor=AppColors.SUCCESS,
                                                           shape=ft.RoundedRectangleBorder(radius=10))),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            def close(e):
                dlg.open = False
                self.page.update()

            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()
        finally:
            db.close()

    def end_session_action(self, session_id):
        db = SessionLocal()
        try:
            session = get_session_by_id(db, session_id)
            if not session:
                return

            dur = int((datetime.now() - session.start_time).total_seconds() / 60)
            cost = round((dur / 60) * (session.station.hourly_rate or 30), 2)

            method_dd = make_dropdown("طريقة الدفع", [
                ("cash", "كاش"), ("vodafone_cash", "فودافون كاش"),
                ("instapay", "إنستاباي"), ("bank_card", "بطاقة بنكية"), ("wallet", "محفظة")
            ], "cash", expand=True)

            discount_field = make_text_field("خصم", "0")

            info = ft.Column([
                ft.Text(f"المدة: {format_duration(dur)}", size=15, weight=ft.FontWeight.W_600),
                ft.Text(f"التكلفة: {format_currency(cost)}", size=15, weight=ft.FontWeight.W_600,
                        color=AppColors.DANGER),
            ], spacing=6)

            def save(e):
                try:
                    end_session(db, session_id)
                    discount = float(discount_field.value or 0)
                    process_session_payment(db, session_id, method_dd.value, discount)
                    dlg.open = False
                    self.page.update()
                    self.refresh()
                    show_snackbar(self.page, "تم إنهاء الجلسة بنجاح", AppColors.SUCCESS)
                except Exception as ex:
                    show_snackbar(self.page, str(ex), AppColors.DANGER)

            dlg = ft.AlertDialog(
                title=ft.Text("إنهاء الجلسة"),
                content=ft.Column([info, method_dd, discount_field], spacing=12, width=400),
                actions=[
                    ft.TextButton("إلغاء", on_click=lambda e: close(e)),
                    ft.ElevatedButton("إنهاء ودفع", on_click=save,
                                      style=ft.ButtonStyle(bgcolor=AppColors.SUCCESS,
                                                           shape=ft.RoundedRectangleBorder(radius=10))),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            def close(e):
                dlg.open = False
                self.page.update()

            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()
        finally:
            db.close()

    def cancel_session_action(self, session_id):
        dlg = make_confirm_dialog(
            "إلغاء الجلسة",
            "هل أنت متأكد من إلغاء هذه الجلسة بدون دفع؟",
            lambda: self._do_cancel(session_id),
            self.page
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _do_cancel(self, session_id):
        db = SessionLocal()
        try:
            cancel_session(db, session_id)
            self.refresh()
            show_snackbar(self.page, "تم إلغاء الجلسة", AppColors.WARNING)
        finally:
            db.close()