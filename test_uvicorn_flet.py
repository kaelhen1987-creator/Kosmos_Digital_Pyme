import flet as ft
import logging
import os
import urllib.request
import threading
import time

def main(page: ft.Page):
    page.add(ft.Text("Hello World"))

def check_server():
    time.sleep(2)
    try:
        urllib.request.urlopen("http://127.0.0.1:8550", timeout=2)
        print("HTTP is UP")
    except Exception as e:
        print("HTTP failed", e)

if "FLET_SERVER_PORT" in os.environ:
    os.environ.pop("FLET_SERVER_PORT")

threading.Thread(target=check_server).start()

print("Calling ft.app with WEB_BROWSER")
ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=8550)
print("Finished!")
