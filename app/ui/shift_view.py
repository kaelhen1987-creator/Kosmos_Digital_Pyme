
import flet as ft
from app.utils.helpers import show_message
import datetime

def build_shift_view(page: ft.Page, model, on_success_callback):
    from app.utils.theme import theme_manager
    BG       = theme_manager.get_color("bg_color")
    SURFACE  = theme_manager.get_color("surface")
    BORDER   = theme_manager.get_color("border")
    PRIMARY  = theme_manager.get_color("primary")
    TEXT     = theme_manager.get_color("text_primary")
    DIM      = theme_manager.get_color("text_secondary")
    NAV      = theme_manager.get_color("nav_bg")      # Azul marino #1e3a5f

    # Color para el teclado: un gris azulado suave que contraste sobre la card blanca
    KEY_BG   = "#e8edf5"   # Gris-azulado claro → contrasta bien sobre SURFACE blanco
    KEY_DEL  = "#fde8e8"   # Rojo muy suave para el botón borrar

    """
    Vista de Apertura de Turno — apertura de caja diaria.
    """

    # ── Estado del monto ──────────────────────────────────────────
    amount_value = [""]

    # ── Campos de UI ──────────────────────────────────────────────
    now = datetime.datetime.now()
    days_es   = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    months_es = ["enero","febrero","marzo","abril","mayo","junio","julio",
                 "agosto","septiembre","octubre","noviembre","diciembre"]
    date_str = f"{days_es[now.weekday()]} {now.day} {months_es[now.month-1]} · {now.strftime('%H:%M')} hrs"

    name_field = ft.TextField(
        hint_text="Nombre del Cajero/a",
        hint_style=ft.TextStyle(color=DIM),
        autofocus=True,
        text_size=16,
        color=TEXT,
        bgcolor=SURFACE,
        border_color=BORDER,
        focused_border_color=PRIMARY,
        border_radius=10,
        filled=True,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        width=300,
    )

    amount_display = ft.Text(
        "$0",
        size=36,
        weight="bold",
        color=NAV,   # Azul marino — contrasta muy bien sobre blanco
        text_align=ft.TextAlign.CENTER,
    )

    amount_label = ft.Text(
        "Fondo de apertura",
        size=12,
        color=DIM,
        text_align=ft.TextAlign.CENTER,
    )

    def update_display():
        val = amount_value[0]
        if val == "":
            amount_display.value = "$0"
        else:
            try:
                amount_display.value = f"${int(val):,}".replace(",", ".")
            except:
                amount_display.value = f"${val}"
        amount_display.update()

    def press_key(key):
        if key == "⌫":
            amount_value[0] = amount_value[0][:-1]
        elif key == "0" and amount_value[0] == "":
            pass  # No permitir cero como primer dígito
        elif len(amount_value[0]) < 10:
            amount_value[0] += key
        update_display()

    def make_key_btn(label):
        if label == "⌫":
            return ft.Container(
                content=ft.Icon(ft.Icons.BACKSPACE_OUTLINED, color=theme_manager.get_color("expense"), size=20),
                bgcolor=KEY_DEL,
                border_radius=10,
                alignment=ft.Alignment(0.0, 0.0),
                width=90, height=56,
                on_click=lambda e: press_key("⌫"),
                ink=True,
                border=ft.border.all(1, "#f5c6c6")
            )
        return ft.Container(
            content=ft.Text(label, size=22, weight="bold", color=NAV),
            bgcolor=KEY_BG,
            border_radius=10,
            alignment=ft.Alignment(0.0, 0.0),
            width=90, height=56,
            on_click=lambda e, k=label: press_key(k),
            ink=True,
            border=ft.border.all(1, "#c8d4e8")
        )

    keypad = ft.Column([
        ft.Row([make_key_btn("7"), make_key_btn("8"), make_key_btn("9")], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([make_key_btn("4"), make_key_btn("5"), make_key_btn("6")], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([make_key_btn("1"), make_key_btn("2"), make_key_btn("3")], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([make_key_btn("0"), make_key_btn("⌫")],                   spacing=8, alignment=ft.MainAxisAlignment.CENTER),
    ], spacing=8)

    def handle_open_shift(e):
        name_val = name_field.value.strip()
        if not name_val:
            show_message(page, "Debe ingresar su nombre", "red")
            return
        val = amount_value[0]
        if not val:
            show_message(page, "Debe ingresar el fondo de apertura", "red")
            return
        try:
            amount = float(val)
            if amount < 0:
                show_message(page, "El monto no puede ser negativo", "red")
                return
            model.iniciar_turno(amount, usuario=name_val)
            show_message(page, f"Turno abierto por {name_val} con ${amount:,.0f}", "green")
            on_success_callback()
        except ValueError:
            show_message(page, "Ingrese un número válido", "red")
        except Exception as ex:
            show_message(page, f"Error: {str(ex)}", "red")

    # ── Turno anterior ────────────────────────────────────────────
    prev_shift_txt = ft.Text("", color=DIM, size=12, text_align=ft.TextAlign.CENTER)
    try:
        prev = model.get_last_closed_turno()
        if prev:
            usr    = prev.get("usuario", "?")
            cierre = prev.get("hora_cierre", "")[:5] if prev.get("hora_cierre") else "--:--"
            total  = prev.get("total_ventas", 0)
            prev_shift_txt.value = f"Turno anterior: {usr} · cierre {cierre} hrs · ${total:,.0f} en ventas"
    except:
        pass

    # ── Card central ─────────────────────────────────────────────
    card = ft.Container(
        content=ft.Column([
            # Logo
            ft.Image(src="kosmos_logo.png", width=80, height=80),
            ft.Text("Apertura de caja", size=26, weight="bold", color=NAV),
            ft.Text(date_str, color=DIM, size=13),
            ft.Container(height=10),
            # Campo nombre
            name_field,
            ft.Container(height=8),
            # Display de monto
            ft.Container(
                content=ft.Column([
                    amount_label,
                    amount_display,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                bgcolor=KEY_BG,
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
                width=300,
                border=ft.border.all(1, "#c8d4e8")
            ),
            ft.Container(height=8),
            # Teclado numérico
            keypad,
            ft.Container(height=16),
            # Botón abrir caja
            ft.FilledButton(
                "Abrir caja",
                on_click=handle_open_shift,
                style=ft.ButtonStyle(
                    bgcolor=PRIMARY, color="white",
                    shape=ft.RoundedRectangleBorder(radius=12),
                    padding=ft.padding.symmetric(horizontal=40, vertical=16)
                ),
                width=300, height=52
            ),
            ft.Container(height=12),
            # Info turno anterior
            prev_shift_txt,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
           alignment=ft.MainAxisAlignment.CENTER,
           spacing=6, tight=True),
        bgcolor="white",
        padding=ft.padding.symmetric(horizontal=40, vertical=32),
        border_radius=20,
        shadow=ft.BoxShadow(
            spread_radius=0, blur_radius=24,
            color=ft.Colors.with_opacity(0.12, "black"),
            offset=ft.Offset(0, 4)
        ),
        border=ft.border.all(1, BORDER),
        alignment=ft.Alignment(0.0, 0.0)
    )

    return ft.Container(
        content=card,
        alignment=ft.Alignment(0.0, 0.0),
        expand=True,
        bgcolor=BG
    )
