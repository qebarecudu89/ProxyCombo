import flet as ft
from .. import config as C
from .. import hooks
from .widgets import big_stat

def build_tabs(ctx):
    page = ctx["page"]

    tab_proxy = ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [ft.Icon(ft.Icons.VPN_LOCK, size=16, color=C.ORANGE),
                             ft.Text("Данные прокси", size=13,
                                     weight=ft.FontWeight.W_700, color=C.TEXT)],
                            spacing=8,
                        ),
                        ft.Container(height=4),
                        ft.Text("Оставь пустым — браузер откроется через обычный интернет",
                                size=10, color=C.SUBTEXT),
                        ft.Container(height=10),
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.WEB, size=14, color=C.ORANGE),
                                ft.Text("Браузер", size=11, color=C.TEXT,
                                        weight=ft.FontWeight.W_600),
                                ft.Container(expand=True),
                                ctx["browser_dropdown"],
                            ],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(height=6),
                        ctx["browser_kill_btn"],
                        ft.Container(height=12),
                        ft.Row([ctx["proxy_host_input"], ctx["proxy_port_input"]],
                               spacing=8),
                        ft.Container(height=8),
                        ft.Row([ctx["proxy_type_input"]], spacing=8),
                        ft.Container(height=8),
                        ft.Row([ctx["proxy_user_input"], ctx["proxy_pass_input"]],
                               spacing=8),
                    ],
                    spacing=0,
                ),
                padding=ft.Padding.all(14), bgcolor=C.BG_CARD,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.3, C.ORANGE)),
                border_radius=14,
            ),
            ft.Container(height=10),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [ft.Icon(ft.Icons.CACHED, size=16, color=C.PINK),
                             ft.Text("Ротация IP", size=13,
                                     weight=ft.FontWeight.W_700, color=C.TEXT)],
                            spacing=8,
                        ),
                        ft.Container(height=4),
                        ft.Text("При наличии пула — переключение по списку. Иначе — по URL.",
                                size=10, color=C.SUBTEXT),
                        ft.Container(height=8),
                        ft.Row(
                            [
                                ft.Text("Авто-ротация (мин):", size=11, color=C.TEXT),
                                ctx["auto_rotate_input"],
                                ft.Text("0 = выкл", size=10, color=C.SUBTEXT),
                            ],
                            spacing=8,
                        ),
                        ft.Container(height=12),
                        ctx["rotation_url_input"],
                        ft.Container(height=10),
                        ctx["rotate_btn"],
                    ],
                    spacing=0,
                ),
                padding=ft.Padding.all(14), bgcolor=C.BG_CARD,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.3, C.PINK)),
                border_radius=14,
            ),
            ft.Container(height=10),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [ft.Icon(ft.Icons.SETTINGS_ETHERNET, size=16,
                                     color=C.SUCCESS),
                             ft.Text("Системный прокси (весь ПК)", size=13,
                                     weight=ft.FontWeight.W_700, color=C.TEXT),
                             ft.Container(expand=True),
                             ctx["sys_proxy_switch"]],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(height=4),
                        ft.Text("Трафик ВСЕХ программ пойдёт через прокси",
                                size=10, color=C.SUBTEXT),
                    ],
                    spacing=0,
                ),
                padding=ft.Padding.all(14), bgcolor=C.BG_CARD,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.3, C.SUCCESS)),
                border_radius=14,
            ),
            ft.Container(height=10),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [ft.Icon(ft.Icons.SPEED, size=16, color=C.CYAN),
                             ft.Text("Скорость релея", size=13,
                                     weight=ft.FontWeight.W_700, color=C.TEXT),
                             ft.Container(expand=True),
                             ctx["mode_switch"]],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(height=4),
                        ft.Text("sing-box — быстро, gost — для сложных прокси",
                                size=10, color=C.SUBTEXT),
                    ],
                    spacing=0,
                ),
                padding=ft.Padding.all(14), bgcolor=C.BG_CARD,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.3, C.CYAN)),
                border_radius=14,
            ),
        ],
        spacing=0, scroll=ft.ScrollMode.AUTO, expand=True,
    )

    def create_url_tile(url, index=None):
        def delete_url(e):
            ctx["url_list"].controls.remove(tile)
            ctx["save_and_refresh"]()
            page.update()

        def on_hover(e):
            hover = e.data == "true"
            tile.border = ft.Border.all(
                1.5,
                ft.Colors.with_opacity(0.7, C.PURPLE) if hover else C.BORDER_SOFT,
            )
            tile.bgcolor = (ft.Colors.with_opacity(0.1, C.PURPLE)
                            if hover else C.BG_INPUT)
            page.update()

        num_label = f"{index}" if index is not None else "•"
        tile = ft.Container(
            content=ft.Row(
                [ft.Container(
                    content=ft.Text(num_label, size=10, color=C.PURPLE,
                                    weight=ft.FontWeight.W_700,
                                    font_family="Consolas"),
                    width=24, height=24,
                    bgcolor=ft.Colors.with_opacity(0.15, C.PURPLE),
                    border_radius=6, alignment=ft.Alignment.CENTER),
                 ft.Text(url, size=11, color=C.TEXT, expand=True,
                         font_family="Consolas", max_lines=1,
                         overflow=ft.TextOverflow.ELLIPSIS, selectable=True),
                 ft.IconButton(icon=ft.Icons.CLOSE, icon_size=13,
                               icon_color=C.DANGER, tooltip="Удалить",
                               on_click=delete_url,
                               style=ft.ButtonStyle(padding=4))],
                spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            bgcolor=C.BG_INPUT, border=ft.Border.all(1.5, C.BORDER_SOFT),
            border_radius=10, data=url, on_hover=on_hover, animate=200,
        )
        return tile

    ctx["create_url_tile"] = create_url_tile

    tab_urls = ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [ft.Icon(ft.Icons.LINK, size=16, color=C.CYAN),
                             ft.Text("Список сайтов", size=13,
                                     weight=ft.FontWeight.W_700, color=C.TEXT),
                             ft.Container(
                                 content=ctx["url_count_text"],
                                 padding=ft.Padding.symmetric(
                                     horizontal=8, vertical=2),
                                 bgcolor=ft.Colors.with_opacity(0.15, C.PURPLE),
                                 border_radius=10,
                             ),
                             ft.Container(expand=True),
                             ft.IconButton(icon=ft.Icons.CONTENT_PASTE,
                                           icon_color=C.PINK, icon_size=20,
                                           tooltip="Вставить из буфера",
                                           on_click=ctx["paste_and_add"],
                                           style=ft.ButtonStyle(padding=4)),
                             ft.IconButton(icon=ft.Icons.CLEAR_ALL,
                                           icon_color=C.DANGER, icon_size=20,
                                           tooltip="Очистить всё",
                                           on_click=ctx["clear_urls"],
                                           style=ft.ButtonStyle(padding=4))],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(height=12),
                        ctx["url_input"],
                        ft.Container(height=12),
                        ft.Container(
                            content=ctx["url_list"],
                            bgcolor=C.BG_DEEP, border_radius=10,
                            padding=ft.Padding.all(6),
                            border=ft.Border.all(1, C.BORDER_SOFT),
                            height=320,
                        ),
                        ft.Container(height=10),
                        ft.Container(
                            content=ft.Row(
                                [ft.Icon(ft.Icons.SHUFFLE, size=14, color=C.PURPLE),
                                 ft.Text("Рандомизация порядка открытия",
                                         size=11, color=C.TEXT),
                                 ft.Container(expand=True),
                                 ctx["randomization_switch"]],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=ft.Padding.all(10),
                            bgcolor=C.BG_INPUT, border_radius=10,
                        ),
                    ],
                    spacing=0,
                ),
                padding=ft.Padding.all(14), bgcolor=C.BG_CARD,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.3, C.CYAN)),
                border_radius=14,
            ),
        ],
        spacing=0, scroll=ft.ScrollMode.AUTO, expand=True,
    )

    async def on_refresh_ip(e=None):
        await ctx["refresh_ip_async"]()

    tab_monitor = ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [ft.Icon(ft.Icons.ANALYTICS, size=16, color=C.CYAN),
                             ft.Text("Монитор сети", size=13,
                                     weight=ft.FontWeight.W_700, color=C.TEXT),
                             ft.Container(expand=True),
                             ft.IconButton(icon=ft.Icons.REFRESH,
                                           icon_color=C.CYAN, icon_size=20,
                                           tooltip="Обновить IP",
                                           on_click=on_refresh_ip,
                                           style=ft.ButtonStyle(padding=4))],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(height=4),
                        ft.Text("Скорость, пинг и текущий IP в реальном времени",
                                size=10, color=C.SUBTEXT),
                        ft.Container(height=14),
                        ft.Row(
                            [big_stat("СКАЧИВАНИЕ", ctx["speed_down_text"],
                                      "KB/s", C.SUCCESS, ft.Icons.ARROW_DOWNWARD),
                             big_stat("ОТДАЧА", ctx["speed_up_text"],
                                      "KB/s", C.PINK, ft.Icons.ARROW_UPWARD)],
                            spacing=8,
                        ),
                        ft.Container(height=8),
                        ft.Row(
                            [big_stat("ПИНГ", ctx["ping_text"],
                                      "мс", C.WARNING, ft.Icons.SPEED),
                             big_stat("ВНЕШНИЙ IP",
                                      ctx["monitor_ip_value"],
                                      "", C.CYAN, ft.Icons.PUBLIC)],
                            spacing=8,
                        ),
                    ],
                    spacing=0,
                ),
                padding=ft.Padding.all(14), bgcolor=C.BG_CARD,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.3, C.CYAN)),
                border_radius=14,
            ),
        ],
        spacing=0, scroll=ft.ScrollMode.AUTO, expand=True,
    )

    tab_log = ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [ft.Icon(ft.Icons.TERMINAL, size=16, color=C.PURPLE),
                             ft.Text("Журнал операций", size=13,
                                     weight=ft.FontWeight.W_700, color=C.TEXT)],
                            spacing=8,
                        ),
                        ft.Container(height=12),
                        ft.Container(
                            content=ctx["log_list"],
                            bgcolor=C.BG_DEEP, border_radius=10,
                            padding=ft.Padding.all(6),
                            border=ft.Border.all(1, C.BORDER_SOFT),
                            height=400,
                        ),
                    ],
                    spacing=0,
                ),
                padding=ft.Padding.all(14), bgcolor=C.BG_CARD,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.3, C.PURPLE)),
                border_radius=14,
            ),
        ],
        spacing=0, scroll=ft.ScrollMode.AUTO, expand=True,
    )

    pages = [tab_proxy, tab_urls, tab_monitor, tab_log]
    labels = [("Прокси", ft.Icons.VPN_LOCK),
              ("Сайты", ft.Icons.LINK),
              ("Монитор", ft.Icons.ANALYTICS),
              ("Лог", ft.Icons.TERMINAL)]
    for fn in hooks.HOOKS.get("custom_tab", []):
        try:
            extra = fn()
            if extra:
                pages.append(extra["column"])
                labels.append((extra["title"], extra["icon"]))
        except Exception:
            pass

    return {"pages": pages, "labels": labels,
            "tabs_container": ft.Container(expand=True)}