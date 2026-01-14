#!/opt/homebrew/bin/python3
import flet as ft
from app.data.database import InventarioModel
from app.ui.pos_view import build_pos_view
from app.ui.inventory_view import build_inventory_view
from app.ui.dashboard_view import build_dashboard_view
from app.ui.clients_view import build_clients_view
from app.utils.helpers import is_mobile

# =============================================================================
# VISTA (FLET UI) - Main Entry Point
# =============================================================================
def main(page: ft.Page):
    page.title = "SOS Digital PyME - POS"
    page.bgcolor = "#f5f5f5"
    page.padding = 0
    # page.scroll = ft.ScrollMode.AUTO  <-- Eliminado para evitar conflictos con layout responsivo

    # Configuración responsive
    page.window.min_width = 350
    page.window.min_height = 600
    
    model = InventarioModel()
    
    # Refs
    main_content = ft.Ref[ft.Container]()
    
    # Navegación con botones simples (más compatible)
    # Variable simple para tracking (no usar Ref con tipos primitivos)
    current_view_index = [0]  # Usar lista para mutabilidad en closure
    
    def switch_tab(index):
        current_view_index[0] = index
        
        # Actualizar contenido
        if index == 0:
            content_container.content = build_pos_view(page, model)
        elif index == 1:
            content_container.content = build_inventory_view(page, model)
        elif index == 2:
            content_container.content = build_dashboard_view(page, model)
        else:
            content_container.content = build_clients_view(page, model)
        
        # Actualizar colores de botones
        for i, btn in enumerate([btn_pos, btn_inv, btn_dash, btn_clients]):
            if i == index:
                btn.bgcolor = "#2196F3"
                btn.color = "white"
            else:
                btn.bgcolor = "white"
                btn.color = "#2196F3"
        
        page.update()
    
    # Botones de navegación (textos cortos para móvil)
    btn_pos = ft.ElevatedButton(
        "Ventas",
        icon="shopping_cart",
        on_click=lambda e: switch_tab(0),
        bgcolor="#2196F3",
        color="white",
        expand=True,
        height=50,
    )
    
    btn_inv = ft.ElevatedButton(
        "Inventario",
        icon="list_alt",
        on_click=lambda e: switch_tab(1),
        bgcolor="white",
        color="#2196F3",
        expand=True,
        height=50,
    )
    
    btn_dash = ft.ElevatedButton(
        "Finanzas",
        icon="dashboard",
        on_click=lambda e: switch_tab(2),
        bgcolor="white",
        color="#2196F3",
        expand=True,
        height=50,
    )

    btn_clients = ft.ElevatedButton(
        "Cuaderno",
        icon="people",
        on_click=lambda e: switch_tab(3),
        bgcolor="white",
        color="#2196F3",
        expand=True,
        height=50,
    )
    
    # Contenedor principal
    content_container = ft.Container(
        expand=True,
        padding=10
    )
    content_container.content = build_pos_view(page, model)
    
    # Layout simple y robusto
    page.add(
        ft.Column([
            # Barra de navegación superior
            ft.Container(
                content=ft.Row([btn_pos, btn_inv, btn_dash, btn_clients], spacing=5),
                bgcolor="#f5f5f5",
                padding=10,
            ),
            # Contenido
            content_container
        ], expand=True, spacing=0)
    )
    page.update()

if __name__ == "__main__":
    import sys
    
    # Soporte para modo web (móvil/navegador)
    if "--web" in sys.argv:
        import socket
        
        # Detectar IP local automáticamente
        try:
            # Creamos un socket dummy para ver qué IP usa para salir a internet
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0)
            # No se conecta realmente, solo busca la ruta
            s.connect(('10.254.254.254', 1))
            local_ip = s.getsockname()[0]
        except Exception:
            local_ip = '127.0.0.1'
        finally:
            s.close()
            
        port = 8000
        if "--port" in sys.argv:
            try:
                port_index = sys.argv.index("--port")
                port = int(sys.argv[port_index + 1])
            except (ValueError, IndexError):
                pass
        
        print(f"\n🌐 Servidor web iniciado en puerto {port}")
        print(f"📱 IPHONE/ANDROID: http://{local_ip}:{port}")
        print(f"💻 LOCALHOST:      http://127.0.0.1:{port}\n")
        
        # host='0.0.0.0' expone el servidor a la red local
        ft.app(main, view=ft.AppView.WEB_BROWSER, port=port, host='0.0.0.0')
    else:
        # Modo desktop (ventana nativa)
        ft.app(main)

