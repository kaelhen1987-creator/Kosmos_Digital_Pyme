import flet as ft  # pyre-ignore
from app.utils.activation import get_request_code, save_activation  # pyre-ignore

BG        = "#121212"
CARD_BG   = "#1e1e1e"
BORDER    = "#2a2a2a"
ACCENT    = "#2196F3"
DIM       = "#888888"

def build_activation_view(page: ft.Page, on_success_callback):
    """
    Pantalla de primer uso: solicita la clave de activación.
    Tema oscuro, con branding Kosmos Digital.
    """
    req_code = get_request_code()

    key_input = ft.TextField(
        label="Clave de Activación",
        hint_text="XXXX-XXXX-XXXX-XXXX",
        hint_style=ft.TextStyle(color="#444444"),
        text_align="center",
        autofocus=True,
        capitalization=ft.TextCapitalization.CHARACTERS,
        bgcolor="#1a1a1a", color="white",
        border_color=ACCENT, focused_border_color=ACCENT,
        border_radius=8, filled=True,
        width=320,
        text_size=18,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )

    error_text = ft.Text("", color="#F44336", size=13)

    def handle_activate(e):
        activation_key = key_input.value.strip()
        if not activation_key:
            error_text.value = "Por favor ingresa la clave de activación."
            error_text.update()
            return

        is_valid, result = save_activation(activation_key)

        if is_valid:
            expiry_date = result
            page.snack_bar = ft.SnackBar(
                ft.Text(f"¡Sistema Activado! Vence: {expiry_date.strftime('%d/%m/%Y')}"),
                bgcolor="#4CAF50"
            )
            page.snack_bar.open = True
            page.update()
            on_success_callback()
        else:
            error_text.value = result
            error_text.update()

    # ── Logo / Branding ─────────────────────────────────────────────
    logo = ft.Container(
        content=ft.Text(
            "K",
            size=52, weight="bold", color="white",
            font_family="monospace"
        ),
        width=90, height=90,
        bgcolor=ACCENT,
        border_radius=20,
        alignment=ft.Alignment(0.0, 0.0),
        shadow=ft.BoxShadow(blur_radius=30, color=ft.Colors.with_opacity(0.5, ACCENT), spread_radius=2)
    )

    # ── Código de solicitud ──────────────────────────────────────────
    code_box = ft.Container(
        content=ft.Column([
            ft.Text("TU CÓDIGO DE SOLICITUD", size=11, weight="bold", color=DIM),
            ft.Container(height=6),
            ft.SelectionArea(
                content=ft.Text(req_code, size=20, weight="bold", color="white", font_family="monospace")
            ),
            ft.Container(height=4),
            ft.Text("Envía este código al soporte para obtener tu clave.", size=11, color=DIM, italic=True),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
        bgcolor=CARD_BG,
        padding=ft.padding.symmetric(horizontal=24, vertical=18),
        border=ft.border.all(1, BORDER),
        border_radius=12,
        width=380,
    )

    # ── Layout central ──────────────────────────────────────────────
    content = ft.Column([
        logo,
        ft.Container(height=18),
        ft.Text("Kosmos Digital PyME", size=28, weight="bold", color="white"),
        ft.Text("Activación de licencia requerida", size=14, color=DIM),
        ft.Container(height=28),
        code_box,
        ft.Container(height=24),
        key_input,
        error_text,
        ft.Container(height=14),
        ft.FilledButton(
            "Activar Sistema",
            icon=ft.Icons.VERIFIED_OUTLINED,
            width=320, height=50,
            style=ft.ButtonStyle(
                bgcolor=ACCENT, color="white",
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            on_click=handle_activate
        ),
        ft.Container(height=20),
        ft.Text("Soporte: kosmos.digital@gmail.com", size=12, color="#555555"),
    ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        expand=True, spacing=4
    )

    return ft.Container(
        content=content,
        bgcolor=BG,
        alignment=ft.Alignment(0.0, 0.0),
        expand=True,
        padding=40
    )
