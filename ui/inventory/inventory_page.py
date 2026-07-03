import flet as ft
from database.db import SessionLocal
from services.services import (
    add_inventory_item, get_inventory, update_inventory_quantity, delete_inventory_item
)
from ui.components.widgets import (
    AppColors, PageTemplate, show_snackbar, make_search_field,
    make_confirm_dialog, make_text_field, make_dropdown, format_currency
)


class InventoryPage(PageTemplate):
    def __init__(self, page):
        super().__init__(page, "إدارة المخزون")

    def build_content(self):
        self.filter_dd = make_dropdown("التصنيف", [
            ("", "الكل"), ("controller", "كنترولر"), ("headset", "هيدفون"),
            ("cable", "كابل"), ("snack", "سناكس"), ("drink", "مشروبات"),
            ("accessory", "إكسسوارات"), ("other", "أخرى"),
        ], "", width=180)
        self.filter_dd.on_change = lambda e: self.refresh()
        self.inventory_list = ft.Column(spacing=6)
        return ft.Column(
            controls=[
                ft.Row([
                    make_search_field(on_change=lambda e: self.refresh(), placeholder="ابحث في المخزون..."),
                    self.filter_dd,
                    ft.ElevatedButton("إضافة صنف", icon=ft.icons.ADD,
                        on_click=lambda e: self.show_form_dialog(),
                        style=ft.ButtonStyle(bgcolor=AppColors.PRIMARY,
                                             shape=ft.RoundedRectangleBorder(radius=10))),
                ], spacing=12),
                ft.Container(height=10),
                ft.Container(content=self.inventory_list, expand=True),
            ],
            spacing=0, expand=True,
        )

    def refresh(self):
        db = SessionLocal()
        try:
            cat = self.filter_dd.value if self.filter_dd.value else None
            items_data = get_inventory(db, category=cat)
            low_stock = [i for i in items_data if i.quantity <= i.min_quantity]
            normal = [i for i in items_data if i.quantity > i.min_quantity]

            rows = []
            if low_stock:
                rows.append(ft.Text("⚠️ أصناف ناقصة", size=14, weight=ft.FontWeight.BOLD,
                                    color=AppColors.DANGER, text_direction=ft.TextDirection.RTL))
                for i in low_stock:
                    rows.append(self._make_item_card(i, is_low=True))

            if normal:
                if low_stock:
                    rows.append(ft.Divider(height=15))
                    rows.append(ft.Text("المخزون", size=14, weight=ft.FontWeight.BOLD,
                                        color=AppColors.TEXT, text_direction=ft.TextDirection.RTL))
                for i in normal:
                    rows.append(self._make_item_card(i, is_low=False))

            if not items_data:
                rows = [ft.Container(content=ft.Text("المخزون فارغ", size=15,
                    color=AppColors.TEXT_SECONDARY, text_direction=ft.TextDirection.RTL),
                    padding=40, alignment=ft.alignment.center, expand=True)]

            self.inventory_list.controls = rows
            self.update()
        finally:
            db.close()

    def _make_item_card(self, item, is_low):
        bg_color = "#fff5f5" if is_low else None
        border_color = AppColors.DANGER if is_low else AppColors.BORDER
        return ft.Card(elevation=1, margin=ft.margin.only(bottom=6),
            content=ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(item.name, size=14, weight=ft.FontWeight.W_500, color=AppColors.TEXT),
                        ft.Text(item.category, size=12, color=AppColors.TEXT_SECONDARY),
                    ], spacing=1, expand=True),
                    ft.Text(f"{item.quantity} / {item.min_quantity}", size=14,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.DANGER if is_low else AppColors.TEXT),
                    ft.Text(format_currency(item.unit_price), size=13, color=AppColors.PRIMARY),
                    ft.IconButton(icon=ft.icons.EDIT, size=18,
                                  on_click=lambda e, iid=item.id: self.show_update_qty(iid)),
                    ft.IconButton(icon=ft.icons.DELETE, size=18, icon_color=AppColors.DANGER,
                                  on_click=lambda e, iid=item.id: self.confirm_delete(iid)),
                ], spacing=12),
                padding=12,
                border=ft.border.all(1, border_color) if is_low else None,
            ))

    def show_form_dialog(self):
        name_f = make_text_field("اسم الصنف")
        cat_dd = make_dropdown("التصنيف", [
            ("controller", "كنترولر"), ("headset", "هيدفون"),
            ("cable", "كابل"), ("snack", "سناكس"), ("drink", "مشروبات"),
            ("accessory", "إكسسوارات"), ("other", "أخرى"),
        ])
        qty_f = make_text_field("الكمية", "10")
        min_f = make_text_field("الحد الأدنى", "5")
        price_f = make_text_field("سعر الوحدة", "0")

        def save(e):
            db = SessionLocal()
            try:
                add_inventory_item(db, name=name_f.value, category=cat_dd.value,
                    quantity=int(qty_f.value or 0), min_quantity=int(min_f.value or 5),
                    unit_price=float(price_f.value or 0))
                dlg.open = False
                self.page.update()
                self.refresh()
                show_snackbar(self.page, "تم إضافة الصنف", AppColors.SUCCESS)
            except Exception as ex:
                show_snackbar(self.page, str(ex), AppColors.DANGER)
            finally:
                db.close()

        dlg = ft.AlertDialog(
            title=ft.Text("إضافة صنف جديد", text_direction=ft.TextDirection.RTL),
            content=ft.Column([name_f, cat_dd, ft.Row([qty_f, min_f], spacing=12), price_f],
                              spacing=12, width=420),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda e: close(e)),
                ft.ElevatedButton("حفظ", on_click=save,
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

    def show_update_qty(self, item_id):
        qty_f = make_text_field("الكمية الجديدة", "0")
        def save(e):
            db = SessionLocal()
            try:
                update_inventory_quantity(db, item_id, int(qty_f.value or 0))
                dlg.open = False
                self.page.update()
                self.refresh()
                show_snackbar(self.page, "تم تحديث الكمية", AppColors.SUCCESS)
            finally:
                db.close()
        dlg = ft.AlertDialog(
            title=ft.Text("تحديث الكمية", text_direction=ft.TextDirection.RTL),
            content=ft.Column([qty_f], spacing=12, width=300),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda e: close(e)),
                ft.ElevatedButton("تحديث", on_click=save,
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

    def confirm_delete(self, item_id):
        dlg = make_confirm_dialog("حذف الصنف", "هل أنت متأكد؟",
                                  lambda: self._do_delete(item_id), self.page)
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _do_delete(self, item_id):
        db = SessionLocal()
        try:
            delete_inventory_item(db, item_id)
            self.refresh()
            show_snackbar(self.page, "تم حذف الصنف", AppColors.DANGER)
        finally:
            db.close()