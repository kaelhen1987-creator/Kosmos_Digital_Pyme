import flet as ft
from app.utils.helpers import show_message

def build_setup_view(page: ft.Page, model, on_success_callback):
    
    # Campos de Texto
    txt_name = ft.TextField(label="Nombre del Negocio (Requerido)", width=400, border_radius=8)
    txt_address = ft.TextField(label="Dirección", width=400, border_radius=8)
    txt_owner = ft.TextField(label="Nombre del Dueño", width=400, border_radius=8)
    txt_phone = ft.TextField(label="Teléfono", width=400, border_radius=8, keyboard_type=ft.KeyboardType.PHONE)
    txt_email = ft.TextField(label="Email", width=400, border_radius=8, keyboard_type=ft.KeyboardType.EMAIL)
    
    def save_config(e):
        if not txt_name.value:
            txt_name.error_text = "El nombre es obligatorio"
            page.update()
            return
            
        try:
            # Guardar en Config
            model.set_config("business_name", txt_name.value)
            model.set_config("business_address", txt_address.value)
            model.set_config("owner_name", txt_owner.value)
            model.set_config("business_phone", txt_phone.value)
            model.set_config("business_email", txt_email.value)
            
            show_message(page, "¡Configuración guardada!", "green")
            
            # Continuar flujo
            on_success_callback()
            
        except Exception as ex:
            show_message(page, f"Error al guardar: {ex}", "red")

    content = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.STORE, size=64, color="#2196F3"),
            ft.Text("¡Bienvenido a Digital PyME!", size=24, weight="bold", color="#2196F3"),
            ft.Text("Configuremos tu negocio para empezar.", size=16, color="grey"),
            ft.Divider(height=20, color="transparent"),
            
            txt_name,
            txt_address,
            txt_owner,
            txt_phone,
            txt_email,
            
            ft.Divider(height=20, color="transparent"),
            ft.FilledButton(
                "Guardar y Continuar", 
                on_click=save_config, 
                width=400, 
                height=50,
                style=ft.ButtonStyle(
                    bgcolor="#2196F3", 
                    color="white", 
                    shape=ft.RoundedRectangleBorder(radius=8)
                )
            )
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.Alignment(0, 0),
        expand=True,
        bgcolor="white",
        padding=20
    )
    
    return content
