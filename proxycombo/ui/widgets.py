import flet as ft
from .. import config as C

def make_field(label, password=False, width=None, expand=False):
    return ft.TextField(
        value="", label=label, password=password,
        can_reveal_password=password,
        border_color=C.BORDER, focused_border_color=C.PURPLE, color=C.TEXT,
        bgcolor=C.BG_INPUT, border_radius=10, text_size=12,
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=12),
        width=width, expand=expand,
    )

def big_stat(label, value_control, unit_text, color, icon):
    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [ft.Icon(icon, size=13, color=color),
                     ft.Text(label, size=9, color=C.SUBTEXT,
                             weight=ft.FontWeight.W_600)],
                    spacing=4,
                ),
                ft.Container(height=6),
                ft.Row(
                    [value_control, ft.Text(unit_text, size=10, color=C.SUBTEXT)],
                    spacing=4, vertical_alignment=ft.CrossAxisAlignment.END,
                ),
            ],
            spacing=0,
        ),
        padding=ft.Padding.symmetric(horizontal=14, vertical=12),
        bgcolor=C.BG_INPUT,
        border=ft.Border.all(1, C.BORDER_SOFT),
        border_radius=12, expand=True,
    )

def make_tab_btn(label, icon, idx, on_click, tab_buttons_ref):
    def _on_click(e):
        on_click(idx, tab_buttons_ref)
    return ft.Container(
        content=ft.Container(
            content=ft.Row(
                [ft.Icon(icon, size=15, color=C.TEXT_DIM),
                 ft.Text(label, size=11, weight=ft.FontWeight.W_600,
                         color=C.TEXT_DIM)],
                spacing=6, alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(vertical=8, horizontal=10),
            border_radius=10, bgcolor=ft.Colors.TRANSPARENT,
            border=ft.Border.all(1.5, ft.Colors.TRANSPARENT),
        ),
        on_click=_on_click, expand=True,
    )

def switch_tab(idx, buttons_list, tabs_container, pages, page):
    for i, b in enumerate(buttons_list):
        active = (i == idx)
        b.content.bgcolor = (ft.Colors.with_opacity(0.18, C.PURPLE)
                             if active else ft.Colors.TRANSPARENT)
        b.content.border = ft.Border.all(
            1.5, C.PURPLE if active else ft.Colors.TRANSPARENT
        )
        if isinstance(b.content.content, ft.Row):
            for c in b.content.content.controls:
                if isinstance(c, ft.Text):
                    c.color = C.PURPLE if active else C.TEXT_DIM
    tabs_container.content = pages[idx] if idx < len(pages) else pages[-1]
    page.update()