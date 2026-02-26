import flet as ft
from datetime import datetime, timedelta
import calendar
import sys
import os

# Importar logica de activacion (compatible con PyInstaller y ejecución normal)
if getattr(sys, 'frozen', False):
    # PyInstaller bundle: agregar la carpeta temporal al path
    sys.path.insert(0, sys._MEIPASS)
else:
    # Modo normal: agregar directorio del script al path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.utils.activation import generate_subscription_key
except ImportError:
    # Fallback dummy for testing if app struct not found
    def generate_subscription_key(req_code, date_str):
        return f"KEY-{req_code}-{date_str}"

def add_months(source_date, months):
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return source_date.replace(year=year, month=month, day=day)

def main(page: ft.Page):
    page.title = "Generador de Licencias - SOS Digital PyME"
    page.window_width = 500
    page.window_height = 600
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 30
    
    # Header
    header = ft.Column([
        ft.Icon(ft.Icons.SECURITY, size=50, color="blue"),
        ft.Text("Generador de Licencias", size=24, weight="bold", color="blue"),
        ft.Text("SOS Digital PyME", size=16, color="grey"),
    ], horizontal_alignment="center", spacing=5)

    # Input: Request Code
    req_code_input = ft.TextField(
        label="Código de Solicitud (Machine ID)", 
        hint_text="XXXX-XXXX...", 
        autofocus=True,
        text_size=16,
        border_color="blue"
    )

    # Input: Custom Days (hidden by default)
    custom_days_input = ft.TextField(
        label="Número de días",
        hint_text="Ej: 15, 30, 90...",
        visible=False,
        keyboard_type=ft.KeyboardType.NUMBER,
        text_size=16,
        border_color="orange"
    )

    def toggle_custom_days(e):
        """Show/hide custom days input based on dropdown selection"""
        try:
            # Flet 0.80+: on_select pasa el valor en e.data
            selected = e.data if hasattr(e, 'data') and e.data else e.control.value
            
            # Update visibility
            custom_days_input.visible = (selected == "custom")
            
            # Explicitly update the input control and the page
            custom_days_input.update()
            page.update()
        except Exception as ex:
            print(f"ERROR in toggle_custom_days: {ex}")

    # Input: Duracion
    duration_dropdown = ft.Dropdown(
        label="Duración de Suscripción",
        options=[
            ft.dropdown.Option("1", "1 Mes"),
            ft.dropdown.Option("3", "3 Meses"),
            ft.dropdown.Option("6", "6 Meses"),
            ft.dropdown.Option("12", "1 Año"),
            ft.dropdown.Option("custom", "Personalizado (Días)"),
            ft.dropdown.Option("99", "De por vida (99 años)"),
        ],
        value="1",
        text_size=16,
    )
    # Asignar evento después de crear (compatible con Flet 0.28+ y 0.80+)
    duration_dropdown.on_change = toggle_custom_days

    # Output: License Key
    key_output = ft.TextField(
        label="Clave de Activación Generada",
        read_only=True,
        text_size=18,
        color="green",
        multiline=True,
        min_lines=2
    )

    expiry_text = ft.Text("", color="grey", size=14)

    def generate_key(e):
        code = req_code_input.value.strip()
        if not code:
            req_code_input.error_text = "Ingrese el código de solicitud"
            req_code_input.update()
            return
        
        req_code_input.error_text = None
        
        try:
            today = datetime.now()
            option = duration_dropdown.value
            
            if option == "1":
                expiry_date = add_months(today, 1)
            elif option == "3":
                expiry_date = add_months(today, 3)
            elif option == "6":
                expiry_date = add_months(today, 6)
            elif option == "12":
                expiry_date = add_months(today, 12)
            elif option == "custom":
                # Custom days option
                days_str = custom_days_input.value.strip()
                if not days_str:
                    custom_days_input.error_text = "Ingrese el número de días"
                    custom_days_input.update()
                    return
                try:
                    days = int(days_str)
                    if days <= 0:
                        raise ValueError("Días debe ser mayor a 0")
                    expiry_date = today + timedelta(days=days)
                    custom_days_input.error_text = None
                except ValueError as ve:
                    custom_days_input.error_text = str(ve)
                    custom_days_input.update()
                    return
            elif option == "99":
                expiry_date = today.replace(year=today.year + 99)
            else:
                expiry_date = add_months(today, 1)

            expiry_str = expiry_date.strftime("%Y%m%d")  # Formato correcto: YYYYMMDD
            
            # Generar Clave
            key = generate_subscription_key(code, expiry_str)
            
            key_output.value = key
            expiry_text.value = f"Vence el: {expiry_date.strftime('%Y-%m-%d')}"
            page.update()
            
            page.set_clipboard(key)
            page.snack_bar = ft.SnackBar(ft.Text("¡Clave copiada al portapapeles!"), bgcolor="green")
            page.snack_bar.open = True
            page.update()

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(ex)}"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    btn_generate = ft.FilledButton(
        "Generar Licencia", 
        icon=ft.Icons.VPN_KEY, 
        style=ft.ButtonStyle(bgcolor="blue", color="white", padding=20),
        width=float("inf"), # Full width
        on_click=generate_key
    )

    page.add(
        ft.Column([
            ft.Container(content=header, alignment=ft.Alignment(0, 0)),
            ft.Divider(height=30, color="transparent"),
            req_code_input,
            ft.Divider(height=10, color="transparent"),
            duration_dropdown,
            custom_days_input,
            ft.Divider(height=20, color="transparent"),
            btn_generate,
            ft.Divider(height=30, color="grey"),
            key_output,
            ft.Container(content=expiry_text, alignment=ft.Alignment(1, 0))
        ])
    )

if __name__ == "__main__":
    ft.app(main)
