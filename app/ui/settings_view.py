import flet as ft
import os
import subprocess
from app.utils.helpers import show_message

def build_settings_view(page: ft.Page, model, on_theme_change=None):
    from app.utils.theme import theme_manager
    BG = theme_manager.get_color("bg_color")
    SURFACE = theme_manager.get_color("surface")
    BORDER = theme_manager.get_color("border")
    PRIMARY = theme_manager.get_color("primary")
    REVENUE = theme_manager.get_color("revenue")
    EXPENSE = theme_manager.get_color("expense")
    TEXT = theme_manager.get_color("text_primary")
    DIM = theme_manager.get_color("text_secondary")
    FIELD_BG = theme_manager.get_color("field_bg")


    original_theme = model.get_config("theme", "LIGHT")
    # ── Tema y Apariencia ──────────────────────────────────────────────
    dd_theme = ft.Dropdown(
        label="Esquema de Colores",
        options=[
            ft.dropdown.Option("LIGHT", text="Claro (Nav Azul, Acentos Naranjas)"),
            ft.dropdown.Option("DARK", text="Oscuro Suave (Nav Gris Oscuro, Acentos Verdes)"),
            ft.dropdown.Option("INTERMEDIATE", text="Intermedio (Nav Guinda, Acentos Naranjas)")
        ],
        value=original_theme,
        color=TEXT, border_radius=8, border_color="#555555",
    )

    # ── Controles de Impresión ─────────────────────────────────────────
    dd_impresora = ft.Dropdown(
        label="Tamaño de Impresora",
        options=[
            ft.dropdown.Option("58mm", text="Ticketera Pequeña (58mm)"),
            ft.dropdown.Option("80mm", text="Ticketera Grande (80mm)")
        ],
        value=model.get_config("tipo_impresora", "58mm"),
        color=TEXT, border_radius=8, border_color="#555555",
    )
    txt_pie_pagina = ft.TextField(
        label="Mensaje de Pie de Página",
        value=model.get_config("ticket_mensaje", "¡Gracias por su preferencia!"),
        bgcolor=SURFACE, color=TEXT, border_color="#555555",
        border_radius=8, filled=True,
    )

    # ── Controles de Datos del Negocio ────────────────────────────────
    txt_name    = ft.TextField(label="Nombre del Negocio",  value=model.get_config("business_name", ""),    bgcolor=SURFACE, color=TEXT, border_color="#555555", filled=True, border_radius=8)
    txt_rut     = ft.TextField(label="RUT de la Empresa",   value=model.get_config("business_rut", ""),     bgcolor=SURFACE, color=TEXT, border_color="#555555", filled=True, border_radius=8)
    txt_address = ft.TextField(label="Dirección",            value=model.get_config("business_address", ""), bgcolor=SURFACE, color=TEXT, border_color="#555555", filled=True, border_radius=8)
    txt_phone   = ft.TextField(label="Teléfono",             value=model.get_config("business_phone", ""),   bgcolor=SURFACE, color=TEXT, border_color="#555555", filled=True, border_radius=8, keyboard_type=ft.KeyboardType.PHONE)
    # ── Controles WiFi / Red ───────────────────────────────────────
    import socket
    def _get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "No disponible"

    wifi_current = model.get_config("wifi_mode", "0") == "1"
    sw_wifi = ft.Switch(
        value=wifi_current,
        active_color=PRIMARY,
    )
    txt_wifi_pin = ft.TextField(
        label="PIN de Acceso (4 dígitos)",
        value=model.get_config("wifi_pin", ""),
        bgcolor=SURFACE, color=TEXT, border_color="#555555",
        border_radius=8, filled=True,
        keyboard_type=ft.KeyboardType.NUMBER,
        max_length=4, width=200,
        password=True, can_reveal_password=True,
    )
    local_ip = _get_local_ip()
    wifi_port = 8550
    if hasattr(page, 'data') and isinstance(page.data, dict):
        wifi_port = page.data.get('wifi_port', 8550)
    
    # ── Reinicio de Aplicación ────────────────────────────────────────
    def show_restart_dialog():
        def do_restart(e):
            import sys
            import os
            import subprocess
            dlg.open = False
            page.update()
            
            try:
                if page.web:
                    show_message(page, "Reiniciando el sistema... En el servidor central se abrirá la aplicación. (Puedes cerrar esta ventana)", "orange")
                    page.update()
                
                # Lanzar la nueva instancia de la aplicación
                subprocess.Popen([sys.executable] + sys.argv)
                
                # Matar forzosamente y al instante el proceso actual (incluye servidor web y ventanas nativas) 
                # para asegurar que se liberen los recursos y puertos sin excepciones por limpiar la UI.
                os._exit(0)
                
            except Exception as ex:
                show_message(page, f"Error al reiniciar: {ex}", "red")

        dlg = ft.AlertDialog(
            title=ft.Text("Reinicio Requerido", color=TEXT, size=18, weight="bold"),
            content=ft.Text("Has cambiado configuraciones que requieren reiniciar la aplicación.\n\n¿Deseas reiniciar ahora? (Asegúrate de no tener operaciones pendientes en curso)", size=14, color=DIM),
            actions=[
                ft.TextButton("Más tarde", on_click=lambda e: setattr(dlg, 'open', False) or page.update()),
                ft.FilledButton(
                    "Reiniciar Ahora",
                    on_click=do_restart,
                    style=ft.ButtonStyle(bgcolor=REVENUE, color="white", shape=ft.RoundedRectangleBorder(radius=6))
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=SURFACE,
            shape=ft.RoundedRectangleBorder(radius=10),
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ── Guardar ───────────────────────────────────────────────────────
    def save_settings(e):
        try:
            # Check if WiFi changed
            old_wifi_mode = model.get_config("wifi_mode", "0")
            old_wifi_pin = model.get_config("wifi_pin", "")
            
            model.set_config("theme",               dd_theme.value)
            model.set_config("tipo_impresora",      dd_impresora.value)
            model.set_config("ticket_mensaje",      txt_pie_pagina.value)
            model.set_config("business_name",       txt_name.value)
            model.set_config("business_rut",        txt_rut.value)
            model.set_config("business_address",    txt_address.value)
            model.set_config("business_phone",      txt_phone.value)
            
            # WiFi settings
            new_wifi_mode = "1" if sw_wifi.value else "0"
            pin_val = txt_wifi_pin.value.strip() if txt_wifi_pin.value else ""
            
            model.set_config("wifi_mode", new_wifi_mode)
            model.set_config("wifi_pin", pin_val)
            
            wifi_changed = (old_wifi_mode != new_wifi_mode) or (old_wifi_pin != pin_val)
            
            show_message(page, "Configuración guardada exitosamente.", "green")
            
            if dd_theme.value != original_theme and on_theme_change:
                on_theme_change()
                
            if wifi_changed:
                show_restart_dialog()
                
        except Exception as ex:
            show_message(page, f"Error al guardar: {ex}", "red")

    # ── Helpers de UI ─────────────────────────────────────────────────
    def setting_row(label, description, control):
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(label, color=TEXT, size=14, weight="bold"),
                    ft.Text(description, color=DIM, size=12)
                ], spacing=2, expand=True),
                control
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=14, horizontal=20),
            border=ft.border.only(bottom=ft.border.BorderSide(1, BORDER))
        )

    def section_label(text):
        return ft.Container(
            content=ft.Text(text.upper(), color=DIM, size=11, weight="bold"),
            padding=ft.padding.only(left=20, top=20, bottom=8)
        )

    # ── Secciones ─────────────────────────────────────────────────────

    section_apariencia = ft.Column([
        section_label("Apariencia Visual"),
        setting_row("Tema de la Aplicación", 
                    "Cambia los colores principales (Se aplicará automáticamente al guardar)", 
                    dd_theme),
    ], spacing=0, scroll=ft.ScrollMode.AUTO)

    section_impresion = ft.Column([
        section_label("Formato de Ticket"),
        setting_row("Tamaño de impresora", "Ajustar según el hardware disponible", dd_impresora),
        section_label("Personalización"),
        setting_row("Mensaje de pie de página", "Texto que aparece al final del ticket", txt_pie_pagina),
    ], spacing=0, scroll=ft.ScrollMode.AUTO)

    section_negocio = ft.Column([
        section_label("Información del Negocio"),
        setting_row("Nombre del negocio", "Aparece en la cabecera del ticket", txt_name),
        setting_row("RUT de la empresa", "Identificación fiscal", txt_rut),
        setting_row("Dirección", "Dirección del local", txt_address),
        setting_row("Teléfono", "Contacto del negocio", txt_phone),
    ], spacing=0, scroll=ft.ScrollMode.AUTO)


    section_respaldo = ft.Column([
        section_label("Respaldo de datos"),
        ft.Container(
            content=ft.Column([
                ft.Text("Base de datos local", color=TEXT, size=14, weight="bold"),
                ft.Text("Ubicación: ~/Documents/Digital_PyME/sos_pyme.db", color=DIM, size=12),
                ft.Container(height=10),
                ft.OutlinedButton(
                    "Abrir carpeta de datos",
                    icon=ft.Icons.FOLDER_OPEN,
                    style=ft.ButtonStyle(side=ft.BorderSide(1, "#555555"), color=TEXT, shape=ft.RoundedRectangleBorder(radius=6)),
                    on_click=lambda e: subprocess.Popen(["open", os.path.expanduser("~/Documents/Digital_PyME")])
                )
            ]),
            padding=20
        )
    ], spacing=0)

    # ── Sección WiFi / Red ───────────────────────────────────────────
    wifi_status_color = "#4CAF50" if wifi_current else DIM
    wifi_status_text = "ACTIVO" if wifi_current else "Desactivado"

    section_wifi = ft.Column([
        section_label("Modo WiFi – Multipunto de Venta"),
        setting_row("Activar Modo WiFi",
                    "Permite conectar otros dispositivos como puntos de venta",
                    sw_wifi),
        setting_row("PIN de Acceso",
                    "Solo los cajeros con este PIN pueden conectarse",
                    txt_wifi_pin),
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.WIFI, color=wifi_status_color, size=20),
                    ft.Text(f"Estado: {wifi_status_text}", color=wifi_status_color, size=14, weight="bold"),
                ], spacing=8),
                ft.Container(height=8),
                ft.Row([
                    ft.Icon(ft.Icons.COMPUTER, color=DIM, size=16),
                    ft.Text(f"IP Local: {local_ip}", color=TEXT, size=13),
                ], spacing=8),
                ft.Row([
                    ft.Icon(ft.Icons.LINK, color=DIM, size=16),
                    ft.Text(f"URL de Conexión: http://{local_ip}:{wifi_port}", color=PRIMARY, size=13, weight="bold",
                            selectable=True),
                ], spacing=8),
                ft.Container(height=12),
                ft.Container(
                    content=ft.Column([
                        ft.Text("¿Cómo usar?", weight="bold", color=TEXT, size=13),
                        ft.Text("1. Active el Modo WiFi y defina un PIN", color=DIM, size=12),
                        ft.Text("2. Guarde y reinicie la aplicación", color=DIM, size=12),
                        ft.Text("3. En el otro dispositivo, abra el navegador", color=DIM, size=12),
                        ft.Text(f"4. Ingrese la URL: http://{local_ip}:{wifi_port}", color=DIM, size=12),
                        ft.Text("5. Ingrese el PIN para acceder al punto de venta", color=DIM, size=12),
                    ], spacing=4),
                    bgcolor=FIELD_BG,
                    padding=16, border_radius=8,
                    border=ft.border.all(1, BORDER),
                ),
                ft.Container(height=8),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE, color="#FF9800", size=16),
                        ft.Text("Requiere reiniciar la app para aplicar cambios.",
                                color="#FF9800", size=12, italic=True),
                    ], spacing=6),
                ),
            ]),
            padding=20
        )
    ], spacing=0, scroll=ft.ScrollMode.AUTO)

    # ── Mapa de secciones ─────────────────────────────────────────────
    sections = [
        ("Datos del negocio", section_negocio),
        ("Apariencia",        section_apariencia),
        ("Impresión",         section_impresion),
        ("WiFi / Red",        section_wifi),
        ("Respaldo",          section_respaldo),
    ]

    current_idx = [0]
    content_area = ft.Container(content=sections[0][1], expand=True)
    nav_buttons = []

    style_active = ft.ButtonStyle(
        bgcolor=SURFACE, color=TEXT,
        shape=ft.RoundedRectangleBorder(radius=6),
        side=ft.BorderSide(2, PRIMARY),
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        alignment=ft.Alignment(-1.0, 0.0)
    )
    style_inactive = ft.ButtonStyle(
        bgcolor="transparent", color=DIM,
        shape=ft.RoundedRectangleBorder(radius=6),
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        alignment=ft.Alignment(-1.0, 0.0)
    )

    def set_section(idx):
        current_idx[0] = idx
        for i, btn in enumerate(nav_buttons):
            btn.style = style_active if i == idx else style_inactive
        content_area.content = sections[idx][1]
        page.update()

    for i, (name, _) in enumerate(sections):
        btn = ft.TextButton(
            content=ft.Text(name, size=13),
            on_click=lambda e, idx=i: set_section(idx),
            style=style_active if i == 0 else style_inactive,
            width=float("inf")
        )
        nav_buttons.append(btn)

    left_nav = ft.Container(
        content=ft.Column([
            ft.Text("AJUSTES", color=DIM, size=10, weight="bold"),
            ft.Container(height=10),
            *nav_buttons,
        ], spacing=4),
        width=220, bgcolor=SURFACE, padding=16,
        border_radius=10, border=ft.border.all(1, BORDER)
    )

    return ft.Container(
        content=ft.Column([
            ft.Row([
                left_nav,
                ft.Container(
                    content=ft.Column([
                        content_area,
                        ft.Divider(color=BORDER),
                        ft.Row([
                            ft.TextButton(
                                "Cancelar",
                                style=ft.ButtonStyle(color=DIM),
                                on_click=lambda e: show_message(page, "Cambios descartados.", "grey")
                            ),
                            ft.FilledButton(
                                "Guardar cambios",
                                on_click=save_settings,
                                style=ft.ButtonStyle(
                                    bgcolor=REVENUE, color="white",
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                )
                            )
                        ], alignment=ft.MainAxisAlignment.END, spacing=10)
                    ], expand=True, spacing=0),
                    expand=True, bgcolor=SURFACE, padding=0,
                    border_radius=10, border=ft.border.all(1, BORDER),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE
                )
            ], spacing=12, expand=True, vertical_alignment=ft.CrossAxisAlignment.START)
        ], expand=True),
        padding=20, expand=True, bgcolor=BG
    )
