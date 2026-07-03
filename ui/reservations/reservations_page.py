import flet as ft
from datetime import datetime
from database.db import SessionLocal
from services.services import (
    create_reservation, get_reservations, update_reservation_status,
    get_customers, get_stations, cancel_reservation
)
from ui.components.widgets import (
    AppColors, PageTemplate, show_snackbar, make_status_chip,
    make_text_field, make_dropdown, format_datetime
)


class ReservationsPage(PageTemplate):
    def __init__(self, page):
        super().__init__(page, "إدارة الحجوزات")

    def build_content(self):
        self.filter_dd = make_dropdown("الحالة", [
            ("", "الكل"), ("pending", "قيد الانتظار"),
            ("confirmed", "مؤكدة"), ("cancelled", "ملغاة"), ("completed", "مكتملة"),
        ], "", width=180)
        self.filter_dd.on_change = lambda e: self.refresh()
        self.reservations_list = ft.Column(spacing=8)
        return ft.Column(
            controls=[
                ft.Row([
                    ft.Container(expand=True),
                    self.filter_dd,
                    ft.ElevatedButton("حجز جديد", icon=ft.icons.EVENT_AVAILABLE,
                        on_click=lambda e: self.show_create_dialog(),
                        style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY,
                                             shape=ft.RoundedRectangleBorder(radius=10))),
                ], spacing=12),
                ft.Container(height=10),
                ft.Container(content=self.reservations_list, expand=True),
            ],
            spacing=0, expand=True,
        )

    def refresh(self):
        db = SessionLocal()
        try:
            status = self.filter_dd.value if self.filter_dd.value else None
            reservations = get_reservations(db, status=status)
            items = []
            for r in reservations:
                cust = r.customer
                st = r.station
                cust_name = cust.name if cust else f"عميل #{r.customer_id}"
                st_name = st.name if st else f"محطة #{r.station_id}"

                items.append(ft.Card(elevation=1, margin=ft.margin.only(bottom=8),
                    content=ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.icons.EVENT, size=22, color=ft.colors.WHITE),
                                width=48, height=48, bgcolor=AppColors.INFO,
                                border_radius=12, alignment=ft.alignment.center,
                            ),
                            ft.Column([
                                ft.Text(f"{cust_name} - {st_name}", size=14,
                                        weight=ft.FontWeight.W_600, color=AppColors.TEXT),
                                ft.Text(f"📅 {format_datetime(r.reserved_date)} | المدة: {r.duration_minutes} دقيقة",
                                        size=12, color=AppColors.TEXT_SECONDARY),
                                ft.Text(r.notes or "", size=11, color=AppColors.TEXT_SECONDARY),
                            ], spacing=2, expand=True),
                            ft.Column([
                                make_status_chip(r.status),
                                ft.Container(height=4),
                                ft.Row([
                                    ft.IconButton(icon=ft.icons.CHECK, size=18, icon_color=AppColors.SUCCESS,
                                        tooltip="تأكيد",
                                        on_click=lambda e, rid=r.id: self.change_status(rid, "confirmed")),
                                    ft.IconButton(icon=ft.icons.CANCEL, size=18, icon_color=AppColors.DANGER,
                                        tooltip="إلغاء",
                                        on_click=lambda e, rid=r.id: self.change_status(rid, "cancelled")),
                                    ft.IconButton(icon=ft.icons.DONE_ALL, size=18, icon_color=AppColors.PRIMARY,
                                        tooltip="مكتملة",
                                        on_click=lambda e, rid=r.id: self.change_status(rid, "completed")),
                                ], spacing=2),
                            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END),
                        ], spacing=12),
                        padding=15)))
            if not items:
                items = [ft.Container(content=ft.Text("لا توجد حجوزات", size=15,
                    color=AppColors.TEXT_SECONDARY, text_direction=ft.TextDirection.RTL),
                    padding=40, alignment=ft.alignment.center, expand=True)]
            self.reservations_list.controls = items
            self.update()
        finally:
            db.close()

    def show_create_dialog(self):
        db = SessionLocal()
        try:
            customers = get_customers(db, active_only=True)
            stations = get_stations(db)
            avail_stations = [s for s in stations if s.status in ("available", "reserved")]

            cust_opts = [(str(c.id), f"{c.name} - {c.phone}") for c in customers]
            st_opts = [(str(s.id), f"{s.name} ({s.console_type})") for s in avail_stations]

            cust_dd = make_dropdown("العميل", cust_opts)
            st_dd = make_dropdown("المحطة", st_opts)
            date_f = ft.DateTimePicker(
                label="تاريخ ووقت الحجز",
                value=datetime.now(),
                border_radius=10, filled=True,
            )
            dur_f = make_text_field("المدة (دقيقة)", "60")
            notes_f = make_text_field("ملاحظات", "", expand=True)

            def save(e):
                db2 = SessionLocal()
                try:
                    create_reservation(db2,
                        customer_id=int(cust_dd.value),
                        station_id=int(st_dd.value),
                        reserved_date=date_f.value,
                        duration_minutes=int(dur_f.value or 60),
                        notes=notes_f.value or None)
                    dlg.open = False
                    self.page.update()
                    self.refresh()
                    show_snackbar(self.page, "تم إنشاء الحجز", AppColors.SUCCESS)
                except Exception as ex:
                    show_snackbar(self.page, str(ex), AppColors.DANGER)
                finally:
                    db2.close()

            dlg = ft.AlertDialog(
                title=ft.Text("حجز جديد", text_direction=ft.TextDirection.RTL),
                content=ft.Column([cust_dd, st_dd, date_f, dur_f, notes_f],
                                  spacing=12, width=420),
                actions=[
                    ft.TextButton("إلغاء", on_click=lambda e: close(e)),
                    ft.ElevatedButton("حجز", on_click=save,
                                      style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY,
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

    def change_status(self, res_id, status):
        db = SessionLocal()
        try:
            update_reservation_status(db, res_id, status)
            self.refresh()
            label = {"confirmed": "تم التأكيد", "cancelled": "تم الإلغاء", "completed": "تم الإكمال"}
            show_snackbar(self.page, label.get(status, "تم التحديث"), AppColors.SUCCESS)
        except Exception as ex:
            show_snackbar(self.page, str(ex), AppColors.DANGER)
        finally:
            db.close()