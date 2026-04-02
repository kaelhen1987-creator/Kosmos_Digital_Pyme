import flet as ft
import flet.fastapi as flet_fastapi
from fastapi import FastAPI
import uvicorn
import threading
import time

def main(page: ft.Page):
    page.add(ft.Text("Hello World. Platform: " + str(page.platform)))

async def dummy_before_main(page):
    pass

def _start_uvicorn():
    app = FastAPI()
    app.mount("/", flet_fastapi.app(main, before_main=dummy_before_main))
    uvicorn.run(app, host="0.0.0.0", port=8552, log_level="error")

threading.Thread(target=_start_uvicorn, daemon=True).start()

print("Launching Native Desktop App...")
ft.app(target=main)
