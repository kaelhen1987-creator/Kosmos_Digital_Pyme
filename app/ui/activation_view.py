import flet as ft
from app.utils.activation import get_request_code, save_activation, get_activation_status

def build_activation_view(page: ft.Page, on_success_callback):
    """
    Construye la vista de activación.
    on_success_callback: Función a llamar cuando la activación es exitosa.
    """
    
    req_code = get_request_code()
    
    key_input = ft.TextField(
        label="Clave de Activación",
        hint_text="XXXX-XXXX-XXXX-XXXX",
        width=300,
        text_align="center",
        autofocus=True,
        capitalization=ft.TextCapitalization.CHARACTERS
    )
    
    error_text = ft.Text("", color="red", size=14)
    
    def handle_activate(e):
        activation_key = key_input.value.strip()
        if not activation_key:
            error_text.value = "Por favor ingresa la clave."
            error_text.update()
            return
            
        is_valid, result = save_activation(activation_key)
        
        if is_valid:
            # Activación exitosa!
            expiry_date = result
            page.snack_bar = ft.SnackBar(ft.Text(f"¡Sistema Activado! Vence: {expiry_date.strftime('%d/%m/%Y')}"), bgcolor="green")
            page.snack_bar.open = True
            page.update()
            
            # Navegar a la siguiente pantalla (Callback)
            on_success_callback()
        else:
            # Mostrar mensaje de error específico (expirado, inválido, etc)
            error_text.value = result 
            error_text.update()

    view = ft.Column(
        [
            ft.Icon(ft.Icons.LOCK_OUTLINE, size=80, color="#2196F3"),
            ft.Text("Activación Requerida", size=30, weight="bold"),
            ft.Text("Este sistema está protegido y requiere activación para este dispositivo.", size=16, color="grey"),
            ft.Container(height=20),
            
            ft.Container(
                content=ft.Column([
                    ft.Text("Tu Código de Solicitud:", size=14),
                    ft.Container(
                                ft.SelectionArea(
                                    content=ft.Text(req_code, size=24, weight="bold", font_family="monospace"),
                                ),
                        bgcolor="#eeeeee",
                        padding=10,
                        border_radius=5,
                    ),
                    ft.Text("Envía este código a soporte para recibir tu clave.", size=12, italic=True),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                border=ft.border.all(1, "#dddddd"),
                border_radius=10,
            ),
            
            ft.Container(height=20),
            key_input,
            error_text,
            ft.Container(height=10),
            
            ft.FilledButton(
                "Activar Sistema",
                icon=ft.Icons.CHECK,
                width=200,
                height=50,
                on_click=handle_activate
            ),
             ft.Container(height=20),
             ft.Text("Soporte: +56 9 XXXX XXXX", color="grey")
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        expand=True
    )
    
    return ft.Container(content=view, alignment=ft.Alignment(0, 0), expand=True)
