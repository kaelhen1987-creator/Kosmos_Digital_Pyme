import flet as ft

def is_mobile(page: ft.Page):
    if page.window.width:
        return page.window.width < 600
    return False

def show_message(page: ft.Page, msg, color="blue"):
    snack = ft.SnackBar(ft.Text(msg, color="white"), bgcolor=color, open=True)
    page.overlay.append(snack)
    page.update()
