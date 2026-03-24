import flet as ft
import os
import subprocess
from app.utils.helpers import show_message

BG       = "#121212"
PANEL_BG = "#1e1e1e"
CARD_BG  = "#2c2c2c"
BORDER   = "#2a2a2a"
DIM      = "#aaaaaa"

def build_settings_view(page: ft.Page, model):

    # ── Controles de Interfaz ──────────────────────────────────────────
    dd_vista_caja = ft.Dropdown(
        label="Modo de Vista Inicial (Ventas)",
        options=[
            ft.dropdown.Option("scanner", text="Modo Escáner (Lista)"),
            ft.dropdown.Option("visual",  text="Modo Visual (Cajas)")
        ],
        value=model.get_config("vista_caja", "scanner"),
        color="white", border_radius=8, border_color="#555555",
    )
    sw_mostrar_iva = ft.Switch(
        value=model.get_config("mostrar_iva", "1") == "1",
        active_color="#4CAF50"
    )
    sw_confirmar_borrar = ft.Switch(
        value=model.get_config("confirmar_borrar", "1") == "1",
        active_color="#4CAF50"
    )
    sw_sonido = ft.Switch(
        value=model.get_config("sonido_scan", "0") == "1",
        active_color="#4CAF50"
    )

    # ── Controles de Impresión ─────────────────────────────────────────
    dd_impresora = ft.Dropdown(
        label="Tamaño de Impresora",
        options=[
            ft.dropdown.Option("58mm", text="Ticketera Pequeña (58mm)"),
            ft.dropdown.Option("80mm", text="Ticketera Grande (80mm)")
        ],
        value=model.get_config("tipo_impresora", "58mm"),
        color="white", border_radius=8, border_color="#555555",
    )
    txt_pie_pagina = ft.TextField(
        label="Mensaje de Pie de Página",
        value=model.get_config("ticket_mensaje", "¡Gracias por su preferencia!"),
        bgcolor=CARD_BG, color="white", border_color="#555555",
        border_radius=8, filled=True,
    )

    # ── Controles de Datos del Negocio ────────────────────────────────
    txt_name    = ft.TextField(label="Nombre del Negocio",  value=model.get_config("business_name", ""),    bgcolor=CARD_BG, color="white", border_color="#555555", filled=True, border_radius=8)
    txt_rut     = ft.TextField(label="RUT de la Empresa",   value=model.get_config("business_rut", ""),     bgcolor=CARD_BG, color="white", border_color="#555555", filled=True, border_radius=8)
    txt_address = ft.TextField(label="Dirección",            value=model.get_config("business_address", ""), bgcolor=CARD_BG, color="white", border_color="#555555", filled=True, border_radius=8)
    txt_phone   = ft.TextField(label="Teléfono",             value=model.get_config("business_phone", ""),   bgcolor=CARD_BG, color="white", border_color="#555555", filled=True, border_radius=8, keyboard_type=ft.KeyboardType.PHONE)

    # ── Controles IVA y Precios ───────────────────────────────────────
    sw_iva_precio = ft.Switch(
        value=model.get_config("precio_incluye_iva", "1") == "1",
        active_color="#4CAF50"
    )
    txt_iva_tasa = ft.TextField(
        label="Tasa IVA (%)",
        value=model.get_config("tasa_iva", "19"),
        bgcolor=CARD_BG, color="white", border_color="#555555",
        filled=True, border_radius=8, width=200,
        keyboard_type=ft.KeyboardType.NUMBER
    )

    # ── Guardar ───────────────────────────────────────────────────────
    def save_settings(e):
        try:
            model.set_config("vista_caja",         dd_vista_caja.value)
            model.set_config("mostrar_iva",         "1" if sw_mostrar_iva.value else "0")
            model.set_config("confirmar_borrar",    "1" if sw_confirmar_borrar.value else "0")
            model.set_config("sonido_scan",         "1" if sw_sonido.value else "0")
            model.set_config("tipo_impresora",      dd_impresora.value)
            model.set_config("ticket_mensaje",      txt_pie_pagina.value)
            model.set_config("business_name",       txt_name.value)
            model.set_config("business_rut",        txt_rut.value)
            model.set_config("business_address",    txt_address.value)
            model.set_config("business_phone",      txt_phone.value)
            model.set_config("precio_incluye_iva",  "1" if sw_iva_precio.value else "0")
            model.set_config("tasa_iva",            txt_iva_tasa.value)
            show_message(page, "Configuración guardada exitosamente.", "green")
        except Exception as ex:
            show_message(page, f"Error al guardar: {ex}", "red")

    # ── Helpers de UI ─────────────────────────────────────────────────
    def setting_row(label, description, control):
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(label, color="white", size=14, weight="bold"),
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
    section_interfaz = ft.Column([
        section_label("Preferencias Visuales"),
        setting_row("Modo de vista inicial (ventas)", "Define cómo se muestra la pantalla al abrir", dd_vista_caja),
        setting_row("Mostrar IVA en pantalla de ventas", "Muestra precio con y sin IVA", sw_mostrar_iva),
        section_label("Comportamiento"),
        setting_row("Sonido al agregar producto", "Beep al escanear código de barras", sw_sonido),
        setting_row("Confirmación antes de eliminar", "Pedir confirmación al borrar ítems", sw_confirmar_borrar),
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

    section_iva = ft.Column([
        section_label("Configuración de IVA"),
        setting_row("Los precios ya incluyen IVA", "Si está activado, el precio ingresado ya lleva IVA incluido", sw_iva_precio),
        setting_row("Tasa de IVA (%)", "Porcentaje de impuesto a aplicar", txt_iva_tasa),
    ], spacing=0, scroll=ft.ScrollMode.AUTO)

    section_seguridad = ft.Column([
        section_label("Seguridad"),
        ft.Container(
            ft.Text("Próximamente: funciones de PIN y roles de usuario.", color=DIM, italic=True),
            padding=20
        )
    ], spacing=0)

    section_notificaciones = ft.Column([
        section_label("Notificaciones"),
        ft.Container(
            ft.Text("Próximamente: alertas de stock crítico y vencimientos.", color=DIM, italic=True),
            padding=20
        )
    ], spacing=0)

    section_respaldo = ft.Column([
        section_label("Respaldo de datos"),
        ft.Container(
            content=ft.Column([
                ft.Text("Base de datos local", color="white", size=14, weight="bold"),
                ft.Text(f"Ubicación: ~/Documents/Digital_PyME/sos_pyme.db", color=DIM, size=12),
                ft.Container(height=10),
                ft.OutlinedButton(
                    "Abrir carpeta de datos",
                    icon=ft.Icons.FOLDER_OPEN,
                    style=ft.ButtonStyle(side=ft.BorderSide(1, "#555555"), color="white", shape=ft.RoundedRectangleBorder(radius=6)),
                    on_click=lambda e: subprocess.Popen(["open", os.path.expanduser("~/Documents/Digital_PyME")])
                )
            ]),
            padding=20
        )
    ], spacing=0)

    # ── Mapa de secciones ─────────────────────────────────────────────
    sections = [
        ("Interfaz",          section_interfaz),
        ("Impresión",         section_impresion),
        ("Datos del negocio", section_negocio),
        ("IVA y precios",     section_iva),
        ("Notificaciones",    section_notificaciones),
        ("Seguridad",         section_seguridad),
        ("Respaldo",          section_respaldo),
    ]

    current_idx = [0]
    content_area = ft.Container(content=sections[0][1], expand=True)
    nav_buttons = []

    style_active = ft.ButtonStyle(
        bgcolor=CARD_BG, color="white",
        shape=ft.RoundedRectangleBorder(radius=6),
        side=ft.BorderSide(2, "#2196F3"),
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        alignment=ft.alignment.center_left
    )
    style_inactive = ft.ButtonStyle(
        bgcolor="transparent", color=DIM,
        shape=ft.RoundedRectangleBorder(radius=6),
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        alignment=ft.alignment.center_left
    )

    def set_section(index):
        current_idx[0] = index
        content_area.content = sections[index][1]
        for i, btn in enumerate(nav_buttons):
            btn.style = style_active if i == index else style_inactive
        page.update()

    for i, (label, _) in enumerate(sections):
        btn = ft.TextButton(
            label,
            style=style_active if i == 0 else style_inactive,
            on_click=lambda e, idx=i: set_section(idx),
            width=float("inf")
        )
        nav_buttons.append(btn)

    left_nav = ft.Container(
        content=ft.Column([
            ft.Text("AJUSTES", color=DIM, size=10, weight="bold"),
            ft.Container(height=10),
            *nav_buttons,
        ], spacing=4),
        width=220, bgcolor=PANEL_BG, padding=16,
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
                                    bgcolor="#4CAF50", color="white",
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                )
                            )
                        ], alignment=ft.MainAxisAlignment.END, spacing=10)
                    ], expand=True, spacing=0),
                    expand=True, bgcolor=PANEL_BG, padding=0,
                    border_radius=10, border=ft.border.all(1, BORDER),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE
                )
            ], spacing=12, expand=True, vertical_alignment=ft.CrossAxisAlignment.START)
        ], expand=True),
        padding=20, expand=True, bgcolor=BG
    )
