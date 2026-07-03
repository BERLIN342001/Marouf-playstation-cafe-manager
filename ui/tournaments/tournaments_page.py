import flet as ft
from datetime import datetime
from database.db import SessionLocal
from services.services import (
    create_tournament, get_tournaments, register_participant,
    get_tournament_participants, update_tournament_status, eliminate_participant,
    get_customers
)
from ui.components.widgets import (
    AppColors, PageTemplate, show_snackbar, make_status_chip,
    make_text_field, make_confirm_dialog, format_currency, format_datetime
)


class TournamentsPage(PageTemplate):
    def __init__(self, page):
        super().__init__(page, "إدارة البطولات")

    def build_content(self):
        self.tournaments_list = ft.Column(spacing=10)
        return ft.Column(
            controls=[
                ft.Row([
                    ft.Container(expand=True),
                    ft.ElevatedButton("إنشاء بطولة", icon=ft.Icons.EMOJI_EVENTS,
                        on_click=lambda e: self.show_create_dialog(),
                        style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY,
                                             shape=ft.RoundedRectangleBorder(radius=10))),
                ]),
                ft.Container(height=10),
                ft.Container(content=self.tournaments_list, expand=True),
            ],
            spacing=0, expand=True,
        )

    def refresh(self):
        db = SessionLocal()
        try:
            tournaments = get_tournaments(db)
            items = []
            for t in tournaments:
                participants = get_tournament_participants(db, t.id)
                registered = len(participants)
                remaining = t.max_players - registered

                items.append(ft.Card(elevation=2, margin=ft.margin.only(bottom=12),
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Column([
                                    ft.Text(t.name, size=16, weight=ft.FontWeight.BOLD, color=AppColors.TEXT),
                                    ft.Text(t.game, size=13, color=AppColors.TEXT_SECONDARY),
                                ], spacing=2, expand=True),
                                make_status_chip(t.status),
                            ], spacing=12),
                            ft.Row([
                                ft.Text(f"📅 {format_datetime(t.start_date)}", size=12,
                                        color=AppColors.TEXT_SECONDARY),
                                ft.Text(f"💰 اشتراك: {format_currency(t.entry_fee)}", size=12,
                                        color=AppColors.PRIMARY),
                                ft.Text(f"🏆 {t.prize or '—'}", size=12, color=AppColors.WARNING),
                                ft.Text(f"👥 {registered}/{t.max_players}", size=12,
                                        color=AppColors.SUCCESS if remaining > 0 else AppColors.DANGER),
                            ], spacing=20),
                            ft.Container(height=8),
                            ft.Row([
                                ft.ElevatedButton("تسجيل لاعب", icon=ft.Icons.PERSON_ADD,
                                    on_click=lambda e, tid=t.id: self.show_register_dialog(tid),
                                    style=ft.ButtonStyle(
                                        bgcolor=AppColors.PRIMARY if remaining > 0 else AppColors.TEXT_SECONDARY,
                                        shape=ft.RoundedRectangleBorder(radius=8))),
                                ft.ElevatedButton("المشاركين", icon=ft.Icons.LIST,
                                    on_click=lambda e, tid=t.id, p=participants: self.show_participants(tid, p),
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
                                ft.ElevatedButton("بدء", icon=ft.Icons.PLAY_ARROW,
                                    on_click=lambda e, tid=t.id: self.change_status(tid, "in_progress"),
                                    style=ft.ButtonStyle(bgcolor=AppColors.SUCCESS,
                                                         shape=ft.RoundedRectangleBorder(radius=8))),
                                ft.ElevatedButton("إنهاء", icon=ft.Icons.CHECK_CIRCLE,
                                    on_click=lambda e, tid=t.id: self.change_status(tid, "completed"),
                                    style=ft.ButtonStyle(bgcolor=AppColors.WARNING,
                                                         shape=ft.RoundedRectangleBorder(radius=8))),
                            ], spacing=8),
                        ], spacing=6),
                        padding=18)))
            if not items:
                items = [ft.Container(content=ft.Text("لا توجد بطولات", size=15,
                    color=AppColors.TEXT_SECONDARY),
                    padding=40, alignment=ft.alignment.center, expand=True)]
            self.tournaments_list.controls = items
            self.update()
        finally:
            db.close()

    def show_create_dialog(self):
        name_f = make_text_field("اسم البطولة", "بطولة فيفا")
        game_f = make_text_field("اللعبة", "FIFA 25")
        max_f = make_text_field("الحد الأقصى للاعبين", "16")
        fee_f = make_text_field("رسوم الاشتراك", "50")
        prize_f = make_text_field("الجائزة", "1000 ج.م")

        def save(e):
            db = SessionLocal()
            try:
                create_tournament(db, name=name_f.value, game=game_f.value,
                    max_players=int(max_f.value or 16),
                    entry_fee=float(fee_f.value or 0), prize=prize_f.value)
                dlg.open = False
                self.page.update()
                self.refresh()
                show_snackbar(self.page, "تم إنشاء البطولة", AppColors.SUCCESS)
            except Exception as ex:
                show_snackbar(self.page, str(ex), AppColors.DANGER)
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("إنشاء بطولة جديدة"),
            content=ft.Column([name_f, game_f, ft.Row([max_f, fee_f], spacing=12), prize_f],
                              spacing=12, width=420),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda e: close(e)),
                ft.ElevatedButton("إنشاء", on_click=save,
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

    def show_register_dialog(self, tournament_id):
        db = SessionLocal()
        try:
            customers = get_customers(db, active_only=True)
            opts = [(str(c.id), f"{c.name} - {c.phone}") for c in customers]
            cust_dd = ft.Dropdown(
                label="العميل", options=[ft.dropdown.Option(key=o[0], text=o[1]) for o in opts],
                border_radius=10, filled=True,
            )

            def save(e):
                db2 = SessionLocal()
                try:
                    register_participant(db2, tournament_id, int(cust_dd.value))
                    dlg.open = False
                    self.page.update()
                    self.refresh()
                    show_snackbar(self.page, "تم تسجيل اللاعب", AppColors.SUCCESS)
                except Exception as ex:
                    show_snackbar(self.page, str(ex), AppColors.DANGER)
                finally:
                    db2.close()

            dlg = ft.AlertDialog(
                title=ft.Text("تسجيل لاعب"),
                content=ft.Column([cust_dd], spacing=12, width=350),
                actions=[
                    ft.TextButton("إلغاء", on_click=lambda e: close(e)),
                    ft.ElevatedButton("تسجيل", on_click=save,
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

    def show_participants(self, tournament_id, participants):
        items = []
        for p in participants:
            name = p.customer.name if p.customer else f"عميل #{p.customer_id}"
            status = "تم الإقصاء" if p.is_eliminated else ("أبطال" if p.rank else "نشط")
            color = AppColors.DANGER if p.is_eliminated else AppColors.SUCCESS
            items.append(ft.ListTile(
                leading=ft.Text(str(p.bracket_position), size=14,
                                weight=ft.FontWeight.BOLD, color=AppColors.TEXT),
                title=ft.Text(name, size=14),
                trailing=ft.Text(status, size=12, color=color),
            ))
        if not items:
            items = [ft.Text("لا يوجد مشاركين", color=AppColors.TEXT_SECONDARY)]

        dlg = ft.AlertDialog(
            title=ft.Text("المشاركين"),
            content=ft.Column(items, spacing=2, width=400),
            actions=[ft.TextButton("إغلاق", on_click=lambda e: close(e))],
        )
        def close(e):
            dlg.open = False
            self.page.update()
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def change_status(self, tournament_id, status):
        db = SessionLocal()
        try:
            update_tournament_status(db, tournament_id, status)
            self.refresh()
            show_snackbar(self.page, "تم تحديث حالة البطولة", AppColors.SUCCESS)
        except Exception as ex:
            show_snackbar(self.page, str(ex), AppColors.DANGER)
        finally:
            db.close()