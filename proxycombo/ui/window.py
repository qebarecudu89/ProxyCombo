import asyncio
import flet as ft
from .. import config as C
from ..system_proxy import restore_system_proxy
from ..relays import stop_relays

def win_btn(icon, on_click, page, danger=False, tooltip=""):
    def on_hover(e):
        hover = e.data == "true"
        if danger and hover:
            e.control.bgcolor = C.DANGER
            e.control.content.color = "white"
        else:
            e.control.bgcolor = (ft.Colors.with_opacity(0.08, C.TEXT) if hover
                                 else ft.Colors.TRANSPARENT)
            e.control.content.color = C.TEXT_DIM
        page.update()
    return ft.Container(
        content=ft.Icon(icon, size=12, color=C.TEXT_DIM),
        width=32, height=24, border_radius=6,
        alignment=ft.Alignment.CENTER,
        on_click=on_click, on_hover=on_hover,
        animate=150, tooltip=tooltip,
    )

def build_title_bar(page):
    def minimize_window(e):
        try:
            page.window.minimized = True
            page.update()
        except Exception:
            pass

    def close_window(e):
        try:
            restore_system_proxy()
            stop_relays()
            asyncio.create_task(page.window.close())
        except Exception:
            pass

    left = ft.Row(
        [ft.Container(
            content=ft.Text("🧹", size=12),
            width=22, height=22,
            gradient=ft.LinearGradient(begin=ft.Alignment.TOP_LEFT,
                                       end=ft.Alignment.BOTTOM_RIGHT,
                                       colors=C.GRAD_PURPLE),
            border_radius=6, alignment=ft.Alignment.CENTER),
         ft.Text("Proxy", size=12, color=C.TEXT, weight=ft.FontWeight.W_600),
         ft.Text("Combo", size=12, color=C.PURPLE, weight=ft.FontWeight.W_600)],
        spacing=5,
    )
    right = ft.Row(
        [win_btn(ft.Icons.REMOVE, minimize_window, page, tooltip="Свернуть"),
         win_btn(ft.Icons.CLOSE, close_window, page, danger=True,
                 tooltip="Закрыть")],
        spacing=1,
    )
    return ft.WindowDragArea(
        content=ft.Container(
            content=ft.Row([left, ft.Container(expand=True), right],
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            bgcolor=C.BG_TITLEBAR, height=32,
        ),
        maximizable=False,
    )

def build_status_bar(status_dot, status_text, ip_text):
    return ft.Container(
        content=ft.Row(
            [status_dot, status_text, ft.Container(expand=True),
             ft.Icon(ft.Icons.PUBLIC, size=12, color=C.CYAN), ip_text],
            spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=14, vertical=8),
        bgcolor=C.BG_TITLEBAR,
    )

def build_action_bar(start_btn_wrapper):
    return ft.Container(
        content=start_btn_wrapper,
        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        bgcolor=C.BG,
    )