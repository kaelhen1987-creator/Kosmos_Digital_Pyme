import flet as ft
import asyncio

async def main(page: ft.Page):
    try:
        val = await page.client_storage.get_async("session_test")
        if not val:
            val = "new_value_" + page.session_id
            await page.client_storage.set_async("session_test", val)
        page.add(ft.Text(f"Stored value: {val}"))
    except Exception as e:
        page.add(ft.Text(f"Error: {e}"))

ft.app(target=main)
