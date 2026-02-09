import flet as ft

def main(page: ft.Page):
    page.add(ft.Text("Hello, Flet!"))
    print("Flet app started successfully")

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
