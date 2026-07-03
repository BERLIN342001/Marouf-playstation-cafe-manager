import flet as ft
from database.db import SessionLocal, init_db, engine
from services.services import (
    get_setting, set_setting, get_hourly_rate,
    create_package, get_packages, delete_package,
    create_station, get_stations, create_game, get_games
)
from ui.components.widgets import (
    AppColors, PageTemplate, show_snackbar, make_text_field,
    make_confirm_dialog, format_currency
)
from sqlalchemy import inspect
import os, shutil


class SettingsPage(PageTemplate):
    def __init__(self, page):
        super().__init__(page, "الإعدادات")

    def build_content(self):
        self.tabs = ft.Tabs(
            selected_index=0,
            on_change=self.on_tab_change,
            tabs=[
                ft.Tab(text="عام", icon=ft.icons.SETTINGS),
                ft.Tab(text="الأسعار", icon=ft.icons.ATTACH_MONEY),
                ft.Tab(text="الباقات", icon=ft.icons.LABEL),
                ft.Tab(text="الألعاب", icon=ft.icons.SPORTS_ESPORTS),
                ft.Tab(text="النظام", icon=ft.icons.BUILD),
            ],
        )
        self.content_area = ft.Container(expand=True, content=ft.Column(spacing=10))
        return ft.Column(controls=[self.tabs, ft.Container(height=10), self.content_area],
                         spacing=0, expand=True)

    def on_tab_change(self, e):
        self.refresh()

    def refresh(self):
        tab = self.tabs.selected_index
        if tab == 0:
            self._general_settings()
        elif tab == 1:
            self._pricing_settings()
        elif tab == 2:
            self._packages_settings()
        elif tab == 3:
            self._games_settings()
        elif tab == 4:
            self._system_settings()
        self.update()

    def _general_settings(self):
        db = SessionLocal()
        try:
            name_val = get_setting(db, "cafe_name", "كافيه بلايستيشن")
            phone_val = get_setting(db, "cafe_phone", "")

            name_f = make_text_field("اسم الكافيه", name_val)
            phone_f = make_text_field("رقم التليفون", phone_val)
            points_f = make_text_field("نقاط كل 10 جنيه", get_setting(db, "points_rate", "1"))

            def save(e):
                db2 = SessionLocal()
                try:
                    set_setting(db2, "cafe_name", name_f.value)
                    set_setting(db2, "cafe_phone", phone_f.value)
                    set_setting(db2, "points_rate", points_f.value)
                    show_snackbar(self.page, "تم حفظ الإعدادات", AppColors.SUCCESS)
                finally:
                    db2.close()

            self.content_area.content = ft.Column([
                ft.Text("الإعدادات العامة", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                name_f, phone_f, points_f,
                ft.ElevatedButton("حفظ", icon=ft.icons.SAVE, on_click=save,
                    style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY,
                                         shape=ft.RoundedRectangleBorder(radius=10))),
            ], spacing=12)
        finally:
            db.close()

    def _pricing_settings(self):
        db = SessionLocal()
        try:
            rate = get_hourly_rate(db)
            weekend_rate = get_setting(db, "weekend_rate", str(rate))
            holiday_rate = get_setting(db, "holiday_rate", str(rate))

            rate_f = make_text_field("سعر الساعة (عادي)", str(rate))
            weekend_f = make_text_field("سعر الساعة (ويكند)", weekend_rate)
            holiday_f = make_text_field("سعر الساعة (أعياد)", holiday_rate)

            def save(e):
                db2 = SessionLocal()
                try:
                    set_setting(db2, "hourly_rate", rate_f.value)
                    set_setting(db2, "weekend_rate", weekend_f.value)
                    set_setting(db2, "holiday_rate", holiday_f.value)
                    # Also update all stations
                    new_rate = float(rate_f.value or 30)
                    from services.services import get_stations, update_station
                    for st in get_stations(db2):
                        update_station(db2, st.id, hourly_rate=new_rate)
                    show_snackbar(self.page, "تم تحديث الأسعار", AppColors.SUCCESS)
                finally:
                    db2.close()

            self.content_area.content = ft.Column([
                ft.Text("إعدادات الأسعار", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                rate_f, weekend_f, holiday_f,
                ft.ElevatedButton("حفظ وتحديث المحطات", icon=ft.icons.SAVE, on_click=save,
                    style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY,
                                         shape=ft.RoundedRectangleBorder(radius=10))),
            ], spacing=12)
        finally:
            db.close()

    def _packages_settings(self):
        db = SessionLocal()
        try:
            packages = get_packages(db)
            items = []
            for p in packages:
                hourly_equiv = round(p.price / p.hours, 2) if p.hours > 0 else 0
                items.append(ft.Card(elevation=1, margin=ft.margin.only(bottom=6),
                    content=ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.LABEL, size=22, color=AppColors.PRIMARY),
                            ft.Column([
                                ft.Text(p.name, size=14, weight=ft.FontWeight.W_600, color=AppColors.TEXT),
                                ft.Text(f"{p.hours} ساعة | {format_currency(p.price)} | ساعة بـ {format_currency(hourly_equiv)}",
                                        size=12, color=AppColors.TEXT_SECONDARY),
                            ], spacing=1, expand=True),
                            ft.IconButton(icon=ft.icons.DELETE, size=18, icon_color=AppColors.DANGER,
                                          on_click=lambda e, pid=p.id: self._delete_package(pid)),
                        ], spacing=12),
                        padding=12)))

            name_f = make_text_field("اسم الباقة", "3 ساعات")
            hours_f = make_text_field("عدد الساعات", "3")
            price_f = make_text_field("السعر", "80")

            def add_pkg(e):
                db2 = SessionLocal()
                try:
                    create_package(db2, name=name_f.value,
                        hours=float(hours_f.value or 1),
                        price=float(price_f.value or 0))
                    self.refresh()
                    show_snackbar(self.page, "تم إضافة الباقة", AppColors.SUCCESS)
                except Exception as ex:
                    show_snackbar(self.page, str(ex), AppColors.DANGER)
                finally:
                    db2.close()

            self.content_area.content = ft.Column([
                ft.Text("الباقات", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
            ] + items + [
                ft.Divider(height=15),
                ft.Text("إضافة باقة جديدة", size=14, weight=ft.FontWeight.W_600),
                ft.Container(height=6),
                ft.Row([name_f, hours_f, price_f], spacing=12),
                ft.ElevatedButton("إضافة", icon=ft.icons.ADD, on_click=add_pkg,
                    style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY,
                                         shape=ft.RoundedRectangleBorder(radius=10))),
            ], spacing=8)
        finally:
            db.close()

    def _delete_package(self, pkg_id):
        db = SessionLocal()
        try:
            delete_package(db, pkg_id)
            self.refresh()
            show_snackbar(self.page, "تم حذف الباقة", AppColors.DANGER)
        finally:
            db.close()

    def _games_settings(self):
        db = SessionLocal()
        try:
            games = get_games(db)
            items = []
            for g in games:
                items.append(ft.Card(elevation=1, margin=ft.margin.only(bottom=4),
                    content=ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.SPORTS_ESPORTS, size=20, color=AppColors.PRIMARY),
                            ft.Text(g.name, size=13, weight=ft.FontWeight.W_500,
                                    color=AppColors.TEXT, expand=True),
                            ft.Text(g.platform, size=12, color=AppColors.TEXT_SECONDARY),
                            ft.Text(f"{g.available_copies}/{g.total_copies}", size=12, color=AppColors.TEXT),
                            ft.IconButton(icon=ft.icons.DELETE, size=16, icon_color=AppColors.DANGER,
                                          on_click=lambda e, gid=g.id: self._delete_game(gid)),
                        ], spacing=10),
                        padding=10)))

            name_f = make_text_field("اسم اللعبة", "")
            plat_f = make_dropdown("المنصة", [("PS5", "PS5"), ("PS4", "PS4")])
            copies_f = make_text_field("عدد النسخ", "1")

            def add_game(e):
                db2 = SessionLocal()
                try:
                    create_game(db2, name=name_f.value, platform=plat_f.value,
                                total_copies=int(copies_f.value or 1))
                    self.refresh()
                    show_snackbar(self.page, "تم إضافة اللعبة", AppColors.SUCCESS)
                except Exception as ex:
                    show_snackbar(self.page, str(ex), AppColors.DANGER)
                finally:
                    db2.close()

            self.content_area.content = ft.Column([
                ft.Text("إدارة الألعاب", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
            ] + items + [
                ft.Divider(height=15),
                ft.Text("إضافة لعبة جديدة", size=14, weight=ft.FontWeight.W_600),
                ft.Container(height=6),
                ft.Row([name_f, plat_f, copies_f], spacing=12),
                ft.ElevatedButton("إضافة", icon=ft.icons.ADD, on_click=add_game,
                    style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY,
                                         shape=ft.RoundedRectangleBorder(radius=10))),
            ], spacing=8)
        finally:
            db.close()

    def _delete_game(self, game_id):
        db = SessionLocal()
        try:
            from services.services import delete_game
            delete_game(db, game_id)
            self.refresh()
            show_snackbar(self.page, "تم حذف اللعبة", AppColors.DANGER)
        finally:
            db.close()

    def _system_settings(self):
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data", "cafe.db")
        db_size = os.path.getsize(db_path) / 1024 if os.path.exists(db_path) else 0

        def reset_db(e):
            def do_reset():
                import database.models as models
                models.Base.metadata.drop_all(bind=engine)
                models.Base.metadata.create_all(bind=engine)
                self.refresh()
                show_snackbar(self.page, "تم إعادة تعيين قاعدة البيانات", AppColors.WARNING)
            dlg = make_confirm_dialog("تحذير!", "سيتم حذف جميع البيانات نهائياً!", do_reset, self.page)
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

        self.content_area.content = ft.Column([
            ft.Text("إعدادات النظام", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            ft.Card(elevation=1, content=ft.Container(
                content=ft.Column([
                    ft.Text("معلومات قاعدة البيانات", size=14, weight=ft.FontWeight.W_600),
                    ft.Container(height=6),
                    ft.Text(f"المسار: {db_path}", size=12, color=AppColors.TEXT_SECONDARY),
                    ft.Text(f"الحجم: {db_size:.1f} كيلوبايت", size=12, color=AppColors.TEXT_SECONDARY),
                ], spacing=4),
                padding=15)),
            ft.Container(height=10),
            ft.ElevatedButton("إعادة تعيين قاعدة البيانات", icon=ft.icons.DELETE_FOREVER,
                on_click=reset_db,
                style=ft.ButtonStyle(bgcolor=AppColors.DANGER,
                                     shape=ft.RoundedRectangleBorder(radius=10))),
            ft.Container(height=10),
            ft.Text("Marouf PlayStation Cafe Manager v1.0", size=12,
                    color=AppColors.TEXT_SECONDARY),
            ft.Text("Built with Python + Flet + SQLite", size=12,
                    color=AppColors.TEXT_SECONDARY),
        ], spacing=8)