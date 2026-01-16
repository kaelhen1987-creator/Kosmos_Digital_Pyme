
import flet as ft
from app.utils.helpers import show_message

def build_shift_view(page: ft.Page, model, on_success_callback):
    """
    Vista de Apertura de Turno (Caja).
    Obliga al usuario a ingresar un monto inicial para poder usar el sistema.
    """
    

    name_field = ft.TextField(
        label="Nombre del Cajero/a",
        hint_text="Ej: Juan Pérez",
        prefix_icon=ft.Icons.PERSON,
        autofocus=True,
        text_size=18,
        width=300,
        border_color="#2196F3",
        color="black",         # Texto visible
        bgcolor="white",       # Fondo claro
        filled=True
    )

    amount_field = ft.TextField(
        label="Dinero en Caja (Apertura) $",
        hint_text="Ej: 5000",
        keyboard_type=ft.KeyboardType.NUMBER,
        text_align="right",
        text_size=24,
        width=300,
        border_color="#2196F3",
        color="black",         # Texto visible
        bgcolor="white",       # Fondo claro
        filled=True
    )

    def handle_open_shift(e):
        try:
            name_val = name_field.value.strip()
            if not name_val:
                show_message(page, "Debe ingresar su nombre", "red")
                return

            val_str = amount_field.value.strip()
            if not val_str:
                show_message(page, "Debe ingresar un monto", "red")
                return
            
            # Validar que sea número positivo
            amount = float(val_str)
            if amount < 0:
                show_message(page, "El monto no puede ser negativo", "red")
                return

            # Iniciar turno en DB
            model.iniciar_turno(amount, usuario=name_val)
            
            show_message(page, f"Turno abierto por {name_val} con ${amount:,.0f}", "green")
            
            # Callback para cambiar a la vista principal
            on_success_callback()
            
        except ValueError:
            show_message(page, "Ingrese un número válido para el monto", "red")
        except Exception as ex:
            show_message(page, f"Error: {str(ex)}", "red")

    # Tarjeta Central
    card = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.POINT_OF_SALE, size=64, color="#2196F3"),
            ft.Text("Apertura de Caja", size=28, weight="bold", color="#333333"),
            ft.Text("Ingrese sus datos para comenzar el turno.", 
                   size=16, color="grey", text_align="center"),
            ft.Divider(height=20, color="transparent"),
            name_field,
            ft.Divider(height=10, color="transparent"),
            amount_field,
            ft.Divider(height=20, color="transparent"),
            ft.FilledButton(
                "ABRIR CAJA",
                icon=ft.Icons.CHECK,
                on_click=handle_open_shift,
                style=ft.ButtonStyle(
                    bgcolor="#2196F3",
                    color="white",
                    padding=20,
                    text_style=ft.TextStyle(size=18, weight="bold")
                ),
                width=300
            )
        ], horizontal_alignment="center", alignment="center"),
        bgcolor="white",
        padding=40,
        border_radius=20,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.2, "black"),
        ),
        alignment=ft.Alignment(0, 0)
    )

    return ft.Container(
        content=card,
        alignment=ft.Alignment(0, 0),
        expand=True,
        bgcolor="#f5f5f5"
    )
