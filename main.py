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
APP_VERSION = "0.11.17"  # Fix: Android Backup Native Share
WIFI_MODE = False  # ACTIVAR PARA MODO WEB/WIFI (IPHONE/ANDROID)
# ----------------------
async def main(page: ft.Page):
    page.title = "Digital PyME"
    page.theme_mode = ft.ThemeMode.LIGHT # Forzar modo claro
    page.bgcolor = "#f5f5f5"
    page.padding = 0
    # page.scroll = ft.ScrollMode.AUTO  <-- Eliminado para evitar conflictos con layout responsivo

    # Configuración responsive
    page.window.min_width = 350
    page.window.min_height = 600
    
    # Usar nueva base de datos
    # DETECCION DE ENTORNO (Empaquetado vs Dev)
    import sys
    import os
    
    db_name = "sos_pyme.db"
    
    if getattr(sys, 'frozen', False):
        # Si está empaquetado (.app/.exe), usar carpeta Documentos para persistencia
        home_dir = os.path.expanduser("~")
        data_dir = os.path.join(home_dir, "Documents", "SOS_Digital_PyME")
        
        # Crear carpeta si no existe
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
            except OSError:
                pass # Si falla, fallback a local
        
        db_path = os.path.join(data_dir, db_name)
    else:
        # Modo Dev: Carpeta actual
        db_path = "sos_pyme.db"

    model = InventarioModel(db_path)
    
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
            import webbrowser
            try:
                has_update, new_ver, update_url = check_for_updates(APP_VERSION, page.platform)
                print(f"Update check result: has_update={has_update}, version={new_ver}, url={update_url}")
                
                if has_update:
                    def show_update_alert():
                        def handle_download(e):
                            print(f"Download button clicked. URL: {update_url}")
                            if update_url:
                                # Intentar abrir directamente primero
                                try:
                                    print(f"Attempting to launch URL: {update_url}")
                                    page.launch_url(update_url)
                                    show_message(page, "Abriendo descarga...", "green")
                                except Exception as launch_error:
                                    print(f"launch_url failed: {launch_error}")
                                    # Si falla, copiar al portapapeles y avisar
                                    try:
                                        page.set_clipboard(update_url)
                                        show_message(page, "URL copiada. Abre Chrome y pega la URL", "orange")
                                    except Exception as clipboard_error:
                                        print(f"clipboard failed: {clipboard_error}")
                                        show_message(page, "Error al abrir descarga", "red")
                            else:
                                show_message(page, "Error: URL no disponible", "red")
                        
                        # Crear SnackBar con botón de descarga
                        snack = ft.SnackBar(
                            content=ft.Row([
                                ft.Icon(ft.Icons.SYSTEM_UPDATE, color="white"),
                                ft.Text(f"¡Nueva versión disponible: {new_ver}!", color="white", weight="bold"),
                            ], alignment=ft.MainAxisAlignment.START),
                            action="DESCARGAR",
                            on_action=handle_download,
                            duration=10000, # 10 segundos
                            bgcolor="#2196F3"
                        )
                        page.overlay.append(snack)
                        snack.open = True
                        page.update()
                    
                    show_update_alert()
            except Exception as e:
                print(f"Update check failed: {e}")
                pass

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
                fecha = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
                biz_name = model.get_config('business_name', 'MiNegocio').replace(" ", "_")
                ruta_origen = db_path 
                nombre_backup = f"Respaldo_SOS_{biz_name}_{fecha}.sqlite"
                
                # --- DETECCION PLATAFORMA ROBUSTA ---
                # Fix: page.platform devuelve un Enum (PagePlatform.ANDROID), convertir a str para comparar
                plat_str = str(page.platform).lower()
                is_android = "android" in plat_str
                
                if not is_android:
                    try:
                        import jnius
                        is_android = True
                    except ImportError:
                        pass
                
                # --- LOGICA ANDROID (JNIUS SHARE) ---
                if is_android:
                    try:
                        from jnius import autoclass, cast
                        
                        # Contexto Android
                        PythonActivity = autoclass('org.kivy.android.PythonActivity')
                        context = cast('android.content.Context', PythonActivity.mActivity)
                        
                        # 1. Copiar a Private Storage (Siempre accesible)
                        # getExternalFilesDir(None) da la ruta privada de la app en /Android/data/...
                        private_dir = context.getExternalFilesDir(None).getAbsolutePath()
                        archivo_final = os.path.join(private_dir, nombre_backup)
                        
                        shutil.copy2(ruta_origen, archivo_final)
                        
                        # 2. Crear URI con FileProvider (Requerido para Android 7+)
                        # Nota: Flet/Kivy suelen configurar un FileProvider por defecto.
                        # Intentaremos primero con envio directo si es < Android 7, o el truco de "StrictMode" para evitar FileProvider setup complejo
                        
                        # "Hack" para evitar FileUriExposedException en prototipos rapidos (No recomendado prod, pero funcional en Kivy simple)
                        StrictMode = autoclass('android.os.StrictMode')
                        VmPolicyBuilder = autoclass('android.os.StrictMode$VmPolicy$Builder')
                        StrictMode.setVmPolicy(VmPolicyBuilder().build())
                        
                        File = autoclass('java.io.File')
                        dest_file = File(archivo_final)
                        import android # Helper de kivy (si disponible)
                        
                        # 3. Crear Intent SEND
                        Intent = autoclass('android.content.Intent')
                        Uri = autoclass('android.net.Uri')
                        
                        intent = Intent()
                        intent.setAction(Intent.ACTION_SEND)
                        
                        # Uri.fromFile es bloqueado en Android 7+ sin el hack de StrictMode arriba
                        uri = Uri.fromFile(dest_file)
                        
                        intent.putExtra(Intent.EXTRA_STREAM, uri)
                        intent.setType("*/*")
                        
                        # 4. Lanzar Chooser
                        chooser = Intent.createChooser(intent, cast('java.lang.CharSequence', __import__("java.lang").lang.String("Guardar Respaldo en...")))
                        PythonActivity.mActivity.startActivity(chooser)
                        
                        show_message(page, "Abriendo menú 'Compartir'...", "green")
                        
                    except Exception as e_android:
                         show_alert("❌ Error Android", f"Fallo al invocar compartir:\n{str(e_android)}", "red")

                # --- LOGICA DESKTOP / IOS (FALLBACK) ---
                else:
                    if page.platform == "ios":
                        # IOS no permite escritura directa facil, aqui idealmente tambien seria Share, 
                        # pero por ahora dejamos la logica original que fallara pero es lo que habia
                        ruta_destino_carpeta = "/storage/emulated/0/Download" # Esto no existe en iOS, fix pendiente
                    else:
                        # Desktop (Mac/Win)
                        ruta_destino_carpeta = os.path.join(os.path.expanduser("~"), "Desktop")

                    ruta_destino_final = os.path.join(ruta_destino_carpeta, "SOS_PyME_Backups")
                    if not os.path.exists(ruta_destino_final):
                        try:
                            os.makedirs(ruta_destino_final)
                        except:
                            ruta_destino_final = ruta_destino_carpeta

                    archivo_final = os.path.join(ruta_destino_final, nombre_backup)

                    if os.path.exists(ruta_origen):
                        shutil.copy2(ruta_origen, archivo_final)
                        msg = f"Archivo guardado en:\n{archivo_final}"
                        show_alert("✅ Respaldo Exitoso", msg)
                    else:
                        show_alert("❌ Error", f"No se encuentra DB:\n{ruta_origen}", "red")

            except Exception as ex:
                show_alert("❌ Error General", f"Plataforma: {page.platform}\nError: {str(ex)}", "red")

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
