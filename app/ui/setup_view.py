import flet as ft  # pyre-ignore
from app.utils.helpers import show_message  # pyre-ignore

BG      = "#121212"
CARD_BG = "#1e1e1e"
BORDER  = "#2a2a2a"
ACCENT  = "#2196F3"
DIM     = "#888888"

def build_setup_view(page: ft.Page, model, on_success_callback):
    page.bgcolor = BG

    txt_name    = ft.TextField(label="Nombre del Negocio (Requerido)", width=380, border_radius=8,
                               bgcolor="#1a1a1a", color="white", border_color=ACCENT,
                               label_style=ft.TextStyle(color=DIM), filled=True)
    txt_address = ft.TextField(label="Dirección", width=380, border_radius=8,
                               bgcolor="#1a1a1a", color="white", border_color="#555",
                               label_style=ft.TextStyle(color=DIM), filled=True)
    txt_owner   = ft.TextField(label="Nombre del Dueño", width=380, border_radius=8,
                               bgcolor="#1a1a1a", color="white", border_color="#555",
                               label_style=ft.TextStyle(color=DIM), filled=True)
    txt_phone   = ft.TextField(label="Teléfono", width=380, border_radius=8,
                               bgcolor="#1a1a1a", color="white", border_color="#555",
                               label_style=ft.TextStyle(color=DIM), filled=True,
                               keyboard_type=ft.KeyboardType.PHONE)

    def save_config(e):
        if not txt_name.value or not txt_name.value.strip():
            txt_name.error_text = "El nombre es obligatorio"
            page.update()
            return
        try:
            model.set_config("business_name", txt_name.value.strip())
            model.set_config("business_address", txt_address.value)
            model.set_config("owner_name", txt_owner.value)
            model.set_config("business_phone", txt_phone.value)
            show_message(page, "¡Configuración guardada!", "green")
            on_success_callback()
        except Exception as ex:
            show_message(page, f"Error al guardar: {ex}", "red")

    logo = ft.Container(
        content=ft.Text("K", size=44, weight="bold", color="white", font_family="monospace"),
        width=80, height=80, bgcolor=ACCENT, border_radius=18, alignment=ft.Alignment(0.0, 0.0),
        shadow=ft.BoxShadow(blur_radius=28, color=ft.Colors.with_opacity(0.45, ACCENT), spread_radius=2)
    )

    card = ft.Container(
        content=ft.Column([
            txt_name,
            txt_address,
            txt_owner,
            txt_phone,
            ft.Container(height=8),
            ft.FilledButton(
                "Guardar y Continuar →",
                on_click=save_config,
                width=380, height=50,
                style=ft.ButtonStyle(
                    bgcolor=ACCENT, color="white",
                    shape=ft.RoundedRectangleBorder(radius=10)
                )
            )
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=CARD_BG,
        padding=ft.padding.symmetric(horizontal=32, vertical=28),
        border=ft.border.all(1, BORDER),
        border_radius=14,
        width=440
    )

    content = ft.Container(
        content=ft.Column([
            logo,
            ft.Container(height=16),
            ft.Text("Kosmos Digital PyME", size=26, weight="bold", color="white"),
            ft.Text("Configuremos tu negocio antes de comenzar.", size=13, color=DIM),
            ft.Container(height=24),
            card,
        ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        ),
        bgcolor=BG,
        alignment=ft.Alignment(0.0, 0.0),
        expand=True,
        padding=40
    )

    return content
