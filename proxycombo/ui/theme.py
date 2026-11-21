import flet as ft
from .. import config as C

page_ref = {"page": None}

def gradient_btn(text, icon, colors, on_click, height=52):
    def on_hover(e):
        try:
            e.control.scale = 1.015 if e.data == "true" else 1.0
            page_ref["page"].update()
        except Exception:
            pass
    return ft.Container(
        content=ft.Row(
            [ft.Icon(icon, color="white", size=19),
             ft.Text(text, size=13, weight=ft.FontWeight.W_700, color="white")],
            alignment=ft.MainAxisAlignment.CENTER, spacing=8,
        ),
        on_click=on_click, on_hover=on_hover,
        padding=ft.Padding.symmetric(vertical=14, horizontal=20),
        gradient=ft.LinearGradient(begin=ft.Alignment.CENTER_LEFT,
                                    end=ft.Alignment.CENTER_RIGHT,
                                    colors=colors),
        border_radius=14, height=height, animate_scale=200, scale=1.0,
        shadow=ft.BoxShadow(blur_radius=20,
                             color=ft.Colors.with_opacity(0.4, colors[0]),
                             offset=ft.Offset(0, 4)),
    )