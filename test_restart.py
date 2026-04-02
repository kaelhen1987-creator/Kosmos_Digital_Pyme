import flet as ft
import sys
import os

def main(page: ft.Page):
    page.add(ft.Text("App running!"))
    def restart(e):
        os.execl(sys.executable, sys.executable, *sys.argv)
    page.add(ft.ElevatedButton("Restart", on_click=restart))

ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8551)
