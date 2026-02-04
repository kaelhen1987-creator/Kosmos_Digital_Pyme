#!/opt/homebrew/bin/python3
import flet as ft
# Imports de compatibilidad eliminados

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
APP_VERSION = "0.11.15"  # Fix: Hotfix for Backup Dialog Crash

# ... (omitted lines) ...

        # --- BACKUP LOGIC ---
        def show_backup_dialog(e=None):
            print("DEBUG: Backup button clicked!")
            import shutil
            import os
            import datetime
            print(f"DEBUG: Platform={page.platform}, DBPath={db_path}")
            
            # Helper para mostrar alertas (Legacy compatible)
            def show_alert(title, message, color="green"):
                def close_dlg(e):
                    dlg.open = False
                    page.update()

                dlg = ft.AlertDialog(
                    title=ft.Text(title),
                    content=ft.Text(message),
                    actions=[
                        ft.TextButton("OK", on_click=close_dlg)
                    ],
                )
                page.overlay.append(dlg)
                dlg.open = True
                page.update()

            try:
                # 1. Definir nombres
                # ... (resto de logica igual hasta verificacion)
                fecha = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
                biz_name = model.get_config('business_name', 'MiNegocio').replace(" ", "_")
                ruta_origen = db_path 
                
                nombre_backup = f"Respaldo_SOS_{biz_name}_{fecha}.sqlite"
                
                # 2. Definir RUTAS
                if page.platform in ["android", "ios"]:
                    ruta_destino_carpeta = "/storage/emulated/0/Download"
                else:
                    ruta_destino_carpeta = os.path.join(os.path.expanduser("~"), "Desktop")

                ruta_destino_final = os.path.join(ruta_destino_carpeta, "SOS_PyME_Backups")
                if not os.path.exists(ruta_destino_final):
                    try:
                        os.makedirs(ruta_destino_final)
                    except:
                        ruta_destino_final = ruta_destino_carpeta

                archivo_final = os.path.join(ruta_destino_final, nombre_backup)

                # 3. Verificar y Copiar
                if os.path.exists(ruta_origen):
                    shutil.copy2(ruta_origen, archivo_final)
                    
                    msg = f"Archivo guardado en:\n{archivo_final}"
                    if page.platform in ["android", "ios"]:
                        msg += "\n\n(Busca en la carpeta Descargas)"
                    
                    show_alert("✅ Respaldo Exitoso", msg)
                else:
                    show_alert("❌ Error", f"No se encuentra la base de datos original:\n{ruta_origen}", "red")

            except PermissionError:
                show_alert("🔒 Falta Permiso", "Ve a Ajustes > Apps > SOS PyME > Permisos > Archivos y ACTIVA 'Gestión de todos los archivos'.", "orange")
            except FileNotFoundError:
                show_alert("❌ Error de Ruta", "La carpeta de destino no existe.", "red")
            except Exception as ex:
                show_alert("❌ Error", f"Ocurrió un error inesperado:\n{str(ex)}", "red")

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
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.BACKUP, color="black"), 
                    title=ft.Text("Copia de Seguridad", color="black"), 
                    subtitle=ft.Text("Guardar / Compartir DB", size=10, color="grey"),
                    on_click=lambda e: show_backup_dialog(e)
                ),
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
            title=ft.Text("Digital PyME"),
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
                # Botones Acciones Globales
                ft.Row([
                    ft.IconButton(ft.Icons.BACKUP, tooltip="Copia de Seguridad", on_click=lambda e: show_backup_dialog(e)),
                    btn_close_global
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor="#e0e0e0",
            padding=5,
        )

        # Layout principal (Columna con botónera y contenido)
        main_layout = ft.Column([
            top_nav_bar,
            content_container,
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

    from app.ui.setup_view import build_setup_view

    def start_flow():
        # 1. Verificar Activación (Hardware Lock)
        if not is_activated():
            page.add(build_activation_view(page, on_success_callback=start_flow))
            return
            
        # 2. Verificar Configuración Inicial (Nombre Negocio)
        biz_name = model.get_config('business_name')
        if not biz_name:
            page.clean()
            page.add(build_setup_view(page, model, on_success_callback=start_flow))
            return

        # 3. Verificar si hay turno abierto
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
    # Soporte para modo web (móvil/navegador)
    # Soporte para modo web (móvil/navegador) - DESACTIVADO TEMPORALMENTE
    # Para activar, usar: if True: ...
    mode = "DESKTOP" 

    if mode == "WEB":
        # Bloque web eliminado/oculto por solicitud
        pass
    else:
        # Modo desktop (ventana nativa)
        ft.app(target=main)
