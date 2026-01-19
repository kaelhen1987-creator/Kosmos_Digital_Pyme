#!/opt/homebrew/bin/python3
import flet as ft
from app.data.database import InventarioModel
from app.ui.pos_view import build_pos_view
from app.ui.inventory_view import build_inventory_view
from app.ui.dashboard_view import build_dashboard_view
from app.ui.clients_view import build_clients_view
from app.ui.shift_view import build_shift_view  # Nueva Vista
from app.ui.reports_view import build_reports_view # Nueva Vista Reportes
from app.utils.helpers import is_mobile

# =============================================================================
# VISTA (FLET UI) - Main Entry Point
# =============================================================================
from app.utils.activation import is_activated
from app.ui.activation_view import build_activation_view
from app.utils.helpers import show_message # Importar helper para mensajes

# --- SYSTEM VERSION ---
APP_VERSION = "0.9.0"  # Versión Inicial
# ----------------------
def main(page: ft.Page):
    page.title = "SOS Digital PyME - POS"
    page.theme_mode = ft.ThemeMode.LIGHT # Forzar modo claro
    page.bgcolor = "#f5f5f5"
    page.padding = 0
    # page.scroll = ft.ScrollMode.AUTO  <-- Eliminado para evitar conflictos con layout responsivo

    # Configuración responsive
    page.window.min_width = 350
    page.window.min_height = 600
    
    # Usar nueva base de datos
    model = InventarioModel("sos_pyme.db")
    
    # ---------------------------------------------------------
    # LAYOUT PRINCIPAL (APP)
    # ---------------------------------------------------------
    def load_main_app():
        page.clean()
        
        # Refs
        main_content = ft.Ref[ft.Container]()
        
        # --- UPDATE CHECK BACKGROUND TASK ---
        from app.utils.updater import check_for_updates
        import threading
        
        def run_update_check():
            has_update, new_ver, update_url = check_for_updates(APP_VERSION)
            if has_update:
                def show_update_alert():
                    # Crear SnackBar con botón de descarga
                    snack = ft.SnackBar(
                        content=ft.Row([
                            ft.Icon(ft.Icons.SYSTEM_UPDATE, color="white"),
                            ft.Text(f"¡Nueva versión disponible: {new_ver}!", color="white", weight="bold"),
                        ], alignment=ft.MainAxisAlignment.START),
                        action="DESCARGAR",
                        action_color="yellow",
                        on_action=lambda e: page.launch_url(update_url),
                        duration=10000, # 10 segundos
                        bgcolor="#2196F3"
                    )
                    page.overlay.append(snack)
                    snack.open = True
                    page.update()
                
                # Flet requiere manipular UI en el hilo principal o con cuidado
                # Usamos page.run_task o simplemente invocamos si estamos en contexto seguro?
                # Como esto corre en hilo aparte, invocar métodos de UI directo puede fallar en algunos backends.
                # Lo más seguro en Flet es modificar UI desde su loop. 
                # Pero en Desktop suele funcionar. Probaremos directo.
                show_update_alert()

        threading.Thread(target=run_update_check, daemon=True).start()


        def handle_logout():
            """Cierra la sesión y vuelve a la pantalla de apertura de caja"""
            page.clean()
            page.appbar = None # Ocultar barra superior en Login/Turno
            page.add(build_shift_view(page, model, on_success_callback=load_main_app))
            page.update()
        
        # Navegación con botones simples (más compatible)
        # Variable simple para tracking (no usar Ref con tipos primitivos)
        current_view_index = [0]  # Usar lista para mutabilidad en closure
        
        # Estado Compartido de la App
        app_state_cart = {} 

        # --- LOGICA CIERRE DE CAJA GLOBAL ---
        def handle_close_turn_global(e):
            # Obtener datos del turno actual para mostrar "Monto Esperado"
            stats = model.get_current_shift_stats()
            monto_esperado = stats["teorico_en_caja"] if stats else 0
            
            # Campo para ingresar monto final
            final_amount_field = ft.TextField(
                label="Dinero Total en Caja",
                hint_text="Monto final contado",
                keyboard_type=ft.KeyboardType.NUMBER,
                text_align="right",
                autofocus=True
            )

            # Texto para mostrar errores o advertencias
            error_text = ft.Text("", color="red", size=12)
            
            def confirm_close(e):
                try:
                    monto_final = 0
                    if final_amount_field.value:
                        monto_final = float(final_amount_field.value)
                    
                    # Validación simple: si hay diferencia, pedir confirmación extra o solo mostrar alerta
                    # Por ahora, si hay diferencia, mostramos un error primero, y si el usuario insiste...
                    diferencia = monto_final - monto_esperado
                    
                    # Si es la primera vez que intenta cerrar con diferencia, mostramos advertencia
                    if abs(diferencia) > 0 and error_text.value == "":
                        msg = f"Diferencia de ${diferencia:,.0f}. Vuelve a confirmar para cerrar igual."
                        error_text.value = msg
                        error_text.update()
                        return # No cerramos, esperamos segunda confirmación
                    
                    # Cerrar Turno en DB
                    model.cerrar_turno(monto_final)
                    
                    dlg_close.open = False
                    page.update()
                    
                    show_message(page, "Turno cerrado correctamente.", "green")
                    
                    # Logout (Volver a ShiftView)
                    handle_logout()
                        
                except ValueError:
                    error_text.value = "Monto inválido"
                    error_text.update()
                except Exception as ex:
                    show_message(page, f"Error: {str(ex)}", "red")
            
            dlg_close = ft.AlertDialog(
                title=ft.Text("Cerrar Turno"),
                content=ft.Column([
                    ft.Text("¿Confirmas que deseas cerrar la caja del día?"),
                    ft.Text(f"Monto Esperado: ${monto_esperado:,.0f}", weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    final_amount_field,
                    error_text,
                    ft.Text("Al confirmar, se cerrará la sesión.", size=12, color="grey")
                ], height=200, tight=True),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: setattr(dlg_close, 'open', False) or page.update()),
                    ft.FilledButton("Confirmar", on_click=confirm_close, style=ft.ButtonStyle(bgcolor="red", color="white"))
                ],
                actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            page.overlay.append(dlg_close)
            dlg_close.open = True
            page.update()

        btn_close_global = ft.FilledButton(
            "Cerrar Caja",
            icon=ft.Icons.LOGOUT,
            style=ft.ButtonStyle(bgcolor="#D32F2F", color="white"),
            on_click=handle_close_turn_global
        ) 

        def switch_tab(index):
            current_view_index[0] = index
            
            # Actualizar contenido
            if index == 0:
                content_container.content = build_pos_view(page, model, shared_cart=app_state_cart)
            elif index == 1:
                content_container.content = build_inventory_view(page, model)
            elif index == 2:
                content_container.content = build_dashboard_view(page, model, on_logout_callback=handle_logout)
            elif index == 3:
                content_container.content = build_clients_view(page, model)
            else:
                content_container.content = build_reports_view(page, model)
            
            # Actualizar colores de botones (Desktop)
            for i, btn in enumerate([btn_pos, btn_inv, btn_dash, btn_clients, btn_reports]):
                if i == index:
                    btn.bgcolor = "#2196F3"
                    btn.color = "white"
                else:
                    btn.bgcolor = "white"
                    btn.color = "#2196F3"
            
            # Sincronizar Drawer (Móvil)
            if page.drawer:
                page.drawer.selected_index = index
                
            page.update()
            # Cerrar drawer si es móvil
            if page.drawer and page.drawer.open:
                 page.close(page.drawer)
        
        # --- DRAWER MANUAL (Custom Stack Implementation) ---
        # Definimos el contenido del drawer
        drawer_content = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text("SOS PyME", size=20, weight="bold", color="white"),
                    bgcolor="#2196F3", padding=20, width=float("inf")
                ),
                ft.ListTile(leading=ft.Icon(ft.Icons.SHOPPING_CART, color="black"), title=ft.Text("Ventas", color="black"), on_click=lambda e: select_drawer_item(0)),
                ft.ListTile(leading=ft.Icon(ft.Icons.LIST_ALT, color="black"), title=ft.Text("Inventario", color="black"), on_click=lambda e: select_drawer_item(1)),
                ft.ListTile(leading=ft.Icon(ft.Icons.DASHBOARD, color="black"), title=ft.Text("Caja", color="black"), on_click=lambda e: select_drawer_item(2)),
                ft.ListTile(leading=ft.Icon(ft.Icons.PEOPLE, color="black"), title=ft.Text("Fiados", color="black"), on_click=lambda e: select_drawer_item(3)),
                ft.ListTile(leading=ft.Icon(ft.Icons.BAR_CHART, color="black"), title=ft.Text("Reportes", color="black"), on_click=lambda e: select_drawer_item(4)),
                ft.Divider(),
                ft.ListTile(leading=ft.Icon(ft.Icons.LOGOUT, color="black"), title=ft.Text("Cerrar Sesión", color="black"), on_click=lambda e: handle_logout_drawer()),
            ], spacing=0),
            bgcolor="white",
            width=280,
            height=float("inf"),
            shadow=ft.BoxShadow(blur_radius=10, color="#80000000"),
        )
        
        # Contenedor deslizante (Drawer Panel)
        drawer_panel = ft.Container(
            content=drawer_content,
            width=280,
            bgcolor="white",
            offset=ft.Offset(-1.1, 0), # Oculto a la izquierda
            animate_offset=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            alignment=ft.Alignment(-1, 0), 
        )
        
        # Scrim (Fondo oscurecido)
        drawer_scrim = ft.Container(
            bgcolor="#80000000",
            expand=True,
            visible=False,
            on_click=lambda e: close_drawer(),
        )

        def select_drawer_item(index):
            switch_tab(index)
            close_drawer()

        def handle_logout_drawer():
            close_drawer()
            handle_close_turn_global(None)

        def show_drawer(e):
            drawer_scrim.visible = True
            drawer_panel.offset = ft.Offset(0, 0)
            page.update()

        def close_drawer():
            drawer_panel.offset = ft.Offset(-1.1, 0)
            drawer_scrim.visible = False
            page.update()

        mobile_appbar = ft.AppBar(
            leading=ft.IconButton(ft.Icons.MENU, on_click=show_drawer),
            leading_width=40,
            title=ft.Text("SOS Digital PyME"),
            center_title=True,
            bgcolor="#2196F3",
            color="white",
            visible=False,
            actions=[
                ft.IconButton(ft.Icons.LOGOUT, tooltip="Cerrar Caja", on_click=handle_close_turn_global)
            ]
        )
        page.appbar = mobile_appbar
        
        # Botones de navegación (textos cortos para móvil)
        def create_nav_btn(text, icon, idx):
            return ft.FilledButton(
                text,
                icon=icon,
                on_click=lambda e: switch_tab(idx),
                style=ft.ButtonStyle(
                    bgcolor="#2196F3" if idx == 0 else "white",
                    color="white" if idx == 0 else "#2196F3",
                    shape=ft.RoundedRectangleBorder(radius=5)
                ),
                expand=True,
                height=50
            )

        btn_pos = create_nav_btn("Ventas", "shopping_cart", 0)
        btn_inv = create_nav_btn("Inventario", "list_alt", 1)
        btn_dash = create_nav_btn("Caja", "dashboard", 2)
        btn_clients = create_nav_btn("Fiados", "people", 3)
        btn_reports = create_nav_btn("Reportes", "bar_chart", 4)
        
        # Contenedor principal
        content_container = ft.Container(
            expand=True,
            padding=10
        )
        content_container.content = build_pos_view(page, model, shared_cart=app_state_cart)
        
        # Contenedor para botones de desktop (referencia para ocultar/mostrar)
        top_nav_bar = ft.Container(
            content=ft.Row([
                # Botonera Navegación
                ft.Row([btn_pos, btn_inv, btn_dash, btn_clients, btn_reports], spacing=2, scroll=ft.ScrollMode.HIDDEN),
                # Botón Cierre Global
                btn_close_global
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor="#e0e0e0",
            padding=5,
        )

        # Layout principal (Columna con botónera y contenido)
        main_layout = ft.Column([
            top_nav_bar,
            content_container
        ], expand=True, spacing=0)

        # STACK PRINCIPAL: Contiene la App + Scrim + Drawer Lateral
        page.add(
            ft.Stack(
                [
                    main_layout,      # Capa 0: App
                    drawer_scrim,     # Capa 1: Fondo oscuro (visible solo al abrir drawer)
                    drawer_panel,     # Capa 2: Panel lateral
                ],
                expand=True
            )
        )
        
        # --- RESPONSIVE HANDLER ---
        last_mode = [None] # 'mobile' o 'desktop'

        def handle_resize(e):
            is_mobile_now = page.width < 600
            current_mode = 'mobile' if is_mobile_now else 'desktop'
            
            # Solo actualizar si cambió el modo (para evitar parpadeos excesivos)
            if current_mode != last_mode[0]:
                last_mode[0] = current_mode
                
                if is_mobile_now:
                    # Modo Móvil
                    top_nav_bar.visible = False
                    mobile_appbar.visible = True
                else:
                    # Modo Desktop
                    top_nav_bar.visible = True
                    mobile_appbar.visible = False
                
                # Forzar reconstrucción de la vista actual para aplicar cambios responsive
                switch_tab(current_view_index[0])
                page.update()
            
        page.on_resize = handle_resize
        handle_resize(None) # Ejecutar inicial
        
        page.update()

    # ---------------------------------------------------------
    # CONTROL DE FLUJO (INICIO)
    # ---------------------------------------------------------

    def start_flow():
        # 1. Verificar Activación (Hardware Lock)
        if not is_activated():
            page.add(build_activation_view(page, on_success_callback=start_flow))
            return

        # 2. Verificar si hay turno abierto
        active_shift = model.get_active_turno()
        
        if active_shift:
            # SI hay turno, vamos directo a la App
            load_main_app()
        else:
            # NO hay turno, mostramos pantalla de Apertura
            page.clean()  # <--- LIMPIAR ANTES DE MOSTRAR
            page.add(build_shift_view(page, model, on_success_callback=load_main_app))

    # Iniciar flujo
    start_flow()

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
        ft.run(main, view=ft.AppView.WEB_BROWSER, port=port, host='0.0.0.0')
    else:
        # Modo desktop (ventana nativa)
        ft.run(main)


