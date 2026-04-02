import flet as ft
def main(page: ft.Page):
    try:
        page.window.min_width = 350
        print("page.window SUCCESS")
    except Exception as e:
        print(f"page.window ERROR: {e}")
    finally:
        page.window.destroy()
ft.app(target=main)
