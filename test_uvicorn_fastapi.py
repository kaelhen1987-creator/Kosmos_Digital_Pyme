import flet as ft
import flet.fastapi as flet_fastapi
from fastapi import FastAPI
import uvicorn
import threading
import time

def main(page: ft.Page):
    page.add(ft.Text("Hello World via Uvicorn"))

def check_server():
    time.sleep(2)
    import urllib.request
    try:
        urllib.request.urlopen("http://127.0.0.1:8552", timeout=2)
        print("HTTP is UP!!!")
    except Exception as e:
        print("HTTP failed", e)

app = FastAPI()
app.mount("/", flet_fastapi.app(main))

print("Starting custom Uvicorn server...")
threading.Thread(target=check_server).start()

uvicorn.run(app, host="0.0.0.0", port=8552, log_level="info")
print("Finished Uvicorn")
