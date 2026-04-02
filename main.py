#!/opt/homebrew/bin/python3
import flet as ft  # pyre-ignore
# Imports de compatibilidad eliminados

# Imports diferidos para que el catch global atrape cualquier ImportError de librerías nativas compiladas.

# --- SYSTEM VERSION ---
# Versión de la App
# v0.12.0 - Modo WiFi Multipunto de Venta
APP_VERSION = "0.12.0"

def _get_free_port(start_port=8550):
    """Busca un puerto libre a partir del start_port para evitar errores del tipo 'address already in use'."""
    import socket
    port = start_port
    while port < start_port + 20: # Buscar hasta en los primeros 20 saltos
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port # El puerto está libre
        except OSError:
            port += 1 # El puerto está ocupado, intentar el siguiente
    return start_port # Default fallback

WIFI_PORT = _get_free_port(8550)
# ----------------------

def _get_local_ip():
    """Detecta la IP local del equipo en la red WiFi."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5) # Evitar que la red atrase el encendido
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def _read_wifi_config():
    """Lee la configuración WiFi directamente de la DB antes de iniciar Flet."""
    import sqlite3, os
    try:
        home_dir = os.path.expanduser("~")
        db_path = os.path.join(home_dir, "Documents", "Digital_PyME", "sos_pyme.db")
        if not os.path.exists(db_path):
            return False, ""
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = 'wifi_mode'")
        row = cursor.fetchone()
        wifi_on = (row and row[0] == '1')
        cursor.execute("SELECT value FROM config WHERE key = 'wifi_pin'")
        row2 = cursor.fetchone()
        wifi_pin = row2[0] if row2 else ""
        conn.close()
        return wifi_on, wifi_pin
    except Exception:
        return False, ""
async def original_main(page: ft.Page):
    from app.utils.theme import theme_manager
    page.title = "Digital PyME"
    page.theme_mode = ft.ThemeMode.LIGHT if theme_manager.current_theme_name == "LIGHT" else ft.ThemeMode.DARK
    page.bgcolor = theme_manager.get_color("bg_color")
    page.padding = 0
    
    # LAZY IMPORTS
    from app.data.database import InventarioModel
    from app.ui.pos_view import build_pos_view
    from app.ui.inventory_view import build_inventory_view
    from app.ui.dashboard_view import build_dashboard_view
    from app.ui.clients_view import build_clients_view
    from app.ui.shift_view import build_shift_view
    from app.ui.reports_view import build_reports_view
    from app.ui.settings_view import build_settings_view
    from app.utils.helpers import is_mobile, show_message
    from app.utils.activation import is_activated
    from app.ui.activation_view import build_activation_view
    # page.scroll = ft.ScrollMode.AUTO  <-- Eliminado para evitar conflictos con layout responsivo

    # Configuración responsive
    page.window.min_width = 350
    page.window.min_height = 600
    
    # Mostrar mensaje inicial de carga ANTES de tocar el sistema de archivos (Evita pantalla blanca durante prompt de MacOS)
    # SOLO EN MODO ESCRITORIO
    is_wifi_mode = isinstance(page.data, dict) and page.data.get('is_wifi', False) if hasattr(page, 'data') else False
    
    # Como la BD no se ha inicializado todavía en este punto del código, 
    # podemos leerlo de los argumentos o dejar que page.web compruebe si es una vista web
    if not page.web:
        loading_view = ft.Container(
            content=ft.Column([
                ft.ProgressRing(color=theme_manager.get_color("primary")),
                ft.Text("Iniciando Digital PyME...", size=18, weight="bold", color=theme_manager.get_color("text_primary")),
                ft.Text("Por favor, concede los permisos de carpeta si el sistema lo solicita.", size=13, color=theme_manager.get_color("text_secondary"), text_align="center")
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            alignment=ft.Alignment(0.0, 0.0),
            expand=True
        )
        page.add(loading_view)
        # Pequeña pausa para asegurar que Flet pinte el UI antes de bloquear el hilo en el sistema de archivos (TCC Dialog)
        import asyncio
        await asyncio.sleep(0.5)
    
    # Usar nueva base de datos
    # DETECCION DE ENTORNO - SIEMPRE usar Documents para persistencia
    # NOTA: sys.frozen NO funciona con Flet builds, así que siempre 
    # guardamos en Documents para que la DB sobreviva reinstalaciones
    import sys
    import os
    import shutil
    
    try:
        db_name = "sos_pyme.db"
        home_dir = os.path.expanduser("~")
        data_dir = os.path.join(home_dir, "Documents", "Digital_PyME")
        
        # MIGRATION: Renombrar carpeta antigua si existe
        old_data_dir = os.path.join(home_dir, "Documents", "SOS_Digital_PyME")
        if os.path.exists(old_data_dir) and not os.path.exists(data_dir):
            try:
                os.rename(old_data_dir, data_dir)
            except Exception as e:
                print(f"Error migrando carpeta de datos: {e}")

        # Crear carpeta si no existe
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
            except OSError:
                pass
        
        db_path = os.path.join(data_dir, db_name)
        
        # MIGRATION: Si existe una DB en la carpeta de instalación, moverla a Documents
        local_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name)
        if os.path.exists(local_db) and not os.path.exists(db_path):
            try:
                shutil.copy2(local_db, db_path)
            except Exception as e:
                print(f"Error migrando DB local: {e}")
        
        model = InventarioModel(db_path)
        print("DEBUG: Database initialized and Migrations verified (V6).")

        # Leer modo WiFi desde config
        is_wifi = model.get_config('wifi_mode', '0') == '1'
        wifi_pin = model.get_config('wifi_pin', '')
        # Guardar session_id persistente para uso en turnos (Usar Local Storage para persistir a través de recargas)
        active_session = None
        if is_wifi:
            try:
                active_session = page.client_storage.get("pos_device_id")
                if not active_session:
                    import uuid
                    active_session = str(uuid.uuid4())
                    page.client_storage.set("pos_device_id", active_session)
            except Exception:
                active_session = getattr(page, 'session_id', None)

        if not hasattr(page, 'data') or page.data is None:
            page.data = {}
        if isinstance(page.data, dict):
            page.data['session_id'] = active_session
            page.data['is_wifi'] = is_wifi
            page.data['wifi_port'] = WIFI_PORT
        else:
            page.data = {'session_id': active_session, 'is_wifi': is_wifi, 'wifi_port': WIFI_PORT}
    except Exception as e:
        import traceback
        err_trace = traceback.format_exc()
        page.add(ft.Text(f"Error Crítico Inicializando DB:\n{e}\n\n{err_trace}", color="red", selectable=True))
        page.update()
        return
    
    # ---------------------------------------------------------
    # LAYOUT PRINCIPAL (APP)
    # ---------------------------------------------------------
    def load_main_app():
        page.clean()

        # --- APLICAR TEMA SELECCIONADO ---
        from app.utils.theme import theme_manager
        current_theme = model.get_config("theme", "LIGHT")
        theme_manager.set_theme(current_theme)
        
        # TODOS los temas provistos por el usuario son formalmente "Light" (fondo claro, texto oscuro)
        page.theme_mode = ft.ThemeMode.LIGHT 
        page.bgcolor = theme_manager.get_color("bg_color")
        
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
                    # IMPORTANTE: Crear el diálogo en el hilo principal de Flet
                    async def show_update_alert_async():
                        async def handle_download(e):
                            print(f"Download button clicked. URL: {update_url}")
                            if update_url:
                                try:
                                    print(f"Attempting to launch URL: {update_url}")
                                    plat = str(page.platform).lower()
                                    if "android" in plat:
                                        # Android: usar launch_url (async)
                                        await page.launch_url_async(update_url)
                                    else:
                                        # Desktop (Mac/Windows): usar webbrowser
                                        import webbrowser
                                        webbrowser.open(update_url)
                                    show_message(page, "Abriendo descarga...", "green")
                                except Exception as launch_error:
                                    print(f"launch_url failed: {launch_error}")
                                    await handle_copy(None)
                            else:
                                show_message(page, "Error: URL no disponible", "red")
                        
                        async def handle_copy(e):
                            try:
                                await page.set_clipboard_async(update_url)
                                show_message(page, "✅ Enlace copiado. Pégalo en tu navegador.", "green")
                            except Exception:
                                try:
                                    page.set_clipboard(update_url)
                                    show_message(page, "✅ Enlace copiado. Pégalo en tu navegador.", "green")
                                except Exception:
                                    show_message(page, "No se pudo copiar el enlace", "red")

                        async def close_dlg(e):
                            dlg.open = False
                            page.update()

                        dlg = ft.AlertDialog(
                            modal=True,
                            title=ft.Row([
                                ft.Icon(ft.Icons.SYSTEM_UPDATE, color="#2196F3"),
                                ft.Text("Actualización Disponible", weight="bold"),
                            ]),
                            content=ft.Column([
                                ft.Text(f"Nueva versión: {new_ver}", size=16, weight="bold", color="#2196F3"),
                                ft.Text("Se recomienda actualizar para obtener mejoras y correcciones.", size=13),
                                ft.Divider(),
                                ft.Text("Si no se abre la descarga, copia el enlace:", size=11, color="grey"),
                                ft.Row([
                                    ft.IconButton(ft.Icons.COPY, tooltip="Copiar enlace", on_click=handle_copy),
                                    ft.Text(update_url or "", size=10, italic=True, 
                                           overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                                ]),
                            ], tight=True, width=450),
                            actions=[
                                ft.TextButton("Más tarde", on_click=close_dlg),
                                ft.FilledButton("DESCARGAR", icon=ft.Icons.DOWNLOAD, on_click=handle_download),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                        )
                        page.overlay.append(dlg)
                        dlg.open = True
                        page.update()
                    
                    page.run_task(show_update_alert_async)
            except Exception as e:
                print(f"Update check failed: {e}")
                pass

        threading.Thread(target=run_update_check, daemon=True).start()


        def handle_logout():
            """Cierra la sesión y vuelve a la pantalla de apertura de caja"""
            page.overlay.clear() # Fix: Limpiar dialogos y snackbars persistentes
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
            _sid = page.data.get('session_id') if isinstance(page.data, dict) else None
            stats = model.get_current_shift_stats(session_id=_sid)
            monto_esperado = stats["teorico_en_caja"] if stats else 0
            
            # Obtener desglose de ventas por método de pago
            desglose = model.obtener_desglose_ventas_turno(session_id=_sid)
            
            # Campo para ingresar monto final
            final_amount_field = ft.TextField(
                label="Dinero Total en Caja",
                hint_text="Monto final contado",
                keyboard_type=ft.KeyboardType.NUMBER,
                text_align="right",
                autofocus=True,
                border_color="#2196F3",
                color="black",
                bgcolor="white",
                filled=True
            )

            # Texto para mostrar errores o advertencias
            error_text = ft.Text("", color="red", size=12)
            
            # Construir tabla de desglose
            desglose_rows = []
            total_ventas = 0.0
            total_pagos_deuda = 0.0
            
            # Iconos y colores por método de pago
            metodos_config = {
                'EFECTIVO': {'icono': '💵', 'color': '#4CAF50'},
                'DEBITO': {'icono': '💳', 'color': '#2196F3'},
                'CREDITO': {'icono': '💳', 'color': '#1976D2'},
                'TRANSFERENCIA': {'icono': '📱', 'color': '#FF9800'},
                'DEUDA': {'icono': '📋', 'color': '#F44336'}
            }
            
            # Sección de VENTAS DIRECTAS
            ventas_data = desglose.get('ventas', {})
            if ventas_data:
                desglose_rows.append(
                    ft.Text("VENTAS DIRECTAS", size=12, weight="bold", color="#666666")
                )
                
                for metodo in ['EFECTIVO', 'DEBITO', 'CREDITO', 'TRANSFERENCIA', 'DEUDA']:
                    if metodo in ventas_data:
                        info = ventas_data[metodo]
                        cantidad = info['cantidad']
                        total = info['total']
                        total_ventas += float(total)  # pyre-ignore
                        
                        config = metodos_config.get(metodo, {'icono': '📊', 'color': '#757575'})
                        
                        desglose_rows.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Text(f"{config['icono']} {metodo}", 
                                           size=14, weight="bold", color=config['color']),
                                    ft.Row([
                                        ft.Text(f"{cantidad} trans.", size=12, color="grey"),
                                        ft.Text(f"${total:,.0f}", size=14, weight="bold")
                                    ], spacing=10)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                padding=ft.padding.symmetric(vertical=5, horizontal=10),
                                bgcolor="#f5f5f5",
                                border_radius=5
                            )
                        )
            
            # Sección de PAGOS DE DEUDA RECIBIDOS
            pagos_data = desglose.get('pagos_deuda', {})
            if pagos_data:
                desglose_rows.append(ft.Divider(height=10, color="transparent"))
                desglose_rows.append(
                    ft.Text("PAGOS DE DEUDA RECIBIDOS", size=12, weight="bold", color="#666666")
                )
                
                for metodo in ['EFECTIVO', 'DEBITO', 'CREDITO', 'TRANSFERENCIA']:
                    if metodo in pagos_data:
                        info = pagos_data[metodo]
                        cantidad = info['cantidad']
                        total = info['total']
                        total_pagos_deuda += float(total)  # pyre-ignore
                        
                        config = metodos_config.get(metodo, {'icono': '📊', 'color': '#757575'})
                        
                        desglose_rows.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Text(f"  {config['icono']} {metodo}", 
                                           size=13, color=config['color']),
                                    ft.Row([
                                        ft.Text(f"{cantidad} trans.", size=11, color="grey"),
                                        ft.Text(f"${total:,.0f}", size=13, weight="bold")
                                    ], spacing=10)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                padding=ft.padding.symmetric(vertical=4, horizontal=10),
                                bgcolor="#f9f9f9",
                                border_radius=5
                            )
                        )
            
            # Si no hay ventas ni pagos, mostrar mensaje
            if not desglose_rows:
                desglose_rows.append(
                    ft.Text("No hay ventas registradas en este turno", 
                           size=12, color="grey", italic=True)
                )
            
            async def confirm_close(e):
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
                    _sid = page.data.get('session_id') if isinstance(page.data, dict) else None
                    model.cerrar_turno(monto_final, session_id=_sid)
                    
                    # Cerrar diálogo primero
                    dlg_close.open = False
                    page.update()
                    
                    # Pequeño delay para asegurar que el diálogo se cierre
                    import asyncio
                    await asyncio.sleep(0.1)
                    
                    # Logout (Volver a ShiftView) - esto limpia el overlay
                    handle_logout()
                        
                except ValueError:
                    error_text.value = "Monto inválido"
                    error_text.update()
                except Exception as ex:
                    show_message(page, f"Error: {str(ex)}", "red")
            
            # Contenido del diálogo con desglose
            dialog_content = ft.Column([
                ft.Text("📊 Desglose de Ventas del Turno", 
                       size=18, weight="bold", color="#333333"),
                ft.Divider(height=10, color="transparent"),
                ft.Container(
                    content=ft.Column(desglose_rows, spacing=5),
                    padding=10,
                    border=ft.border.all(1, "#e0e0e0"),
                    border_radius=10,
                    bgcolor="white"
                ),
                ft.Divider(height=10, color="transparent"),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("TOTAL VENTAS:", size=14, weight="bold"),
                            ft.Text(f"${total_ventas:,.0f}", size=16, weight="bold", color="#2196F3")
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([
                            ft.Text("Pagos Deuda Recibidos:", size=12, color="grey"),
                            ft.Text(f"${total_pagos_deuda:,.0f}", size=14, weight="bold", color="#4CAF50")
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN) if total_pagos_deuda > 0 else ft.Container(),
                        ft.Divider(height=5, color="#e0e0e0"),
                        ft.Row([
                            ft.Text("Efectivo Esperado:", size=12, color="grey"),
                            ft.Text(f"${monto_esperado:,.0f}", size=14, weight="bold", color="#4CAF50")
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ], spacing=5),
                    padding=10,
                    bgcolor="#f9f9f9",
                    border_radius=5
                ),
                ft.Divider(height=10, color="transparent"),
                final_amount_field,
                error_text,
                ft.Text("Al confirmar, se cerrará la sesión.", size=12, color="grey", italic=True)
            ], tight=True, scroll=ft.ScrollMode.AUTO)
            
            dlg_close = ft.AlertDialog(
                title=ft.Text("Cerrar Turno", size=20, weight="bold"),
                content=ft.Container(
                    content=dialog_content,
                    width=400,
                    height=500
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: setattr(dlg_close, 'open', False) or page.update()),
                    ft.FilledButton("Confirmar Cierre", on_click=confirm_close, 
                                   style=ft.ButtonStyle(bgcolor="#D32F2F", color="white"))
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
            elif index == 4:
                content_container.content = build_reports_view(page, model)
            else:
                content_container.content = build_settings_view(page, model, on_theme_change=load_main_app)
            
            # Actualizar colores de botones (Desktop)
            for i, btn in enumerate([btn_pos, btn_inv, btn_dash, btn_clients, btn_reports, btn_settings]):
                if i == index:
                    btn.style = ft.ButtonStyle(
                        bgcolor=ft.Colors.with_opacity(0.22, "white"),
                        color="white",
                        overlay_color=ft.Colors.with_opacity(0.15, "white"),
                        side=ft.BorderSide(0, "transparent"),
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.padding.symmetric(horizontal=14, vertical=8)
                    )
                else:
                    btn.style = ft.ButtonStyle(
                        bgcolor="transparent",
                        color=ft.Colors.with_opacity(0.75, "white"),
                        overlay_color=ft.Colors.with_opacity(0.18, "white"),
                        side=ft.BorderSide(0, "transparent"),
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.padding.symmetric(horizontal=14, vertical=8)
                    )
            
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
                nombre_backup = f"Respaldo_Digital_{biz_name}_{fecha}.sqlite"
                
                # --- DETECCION PLATAFORMA ROBUSTA ---
                # Fix: page.platform devuelve un Enum (PagePlatform.ANDROID), convertir a str para comparar
                plat_str = str(page.platform).lower()
                is_android = "android" in plat_str
                
                # --- LOGICA SOLO DESKTOP ---
                if is_android:
                     show_message(page, "La función de Backup solo está disponible en la versión de PC (Windows/Mac).", "orange")
                     return

                # --- LOGICA DESKTOP (Mac/Win) ---
                if page.platform == "ios":
                     show_message(page, "Backup no disponible en iOS.", "orange")
                     return

                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                backup_dir = os.path.join(desktop, "Digital_PyME_Backups")
                if not os.path.exists(backup_dir):
                    try:
                        os.makedirs(backup_dir)
                    except:
                        pass

                archivo_final = os.path.join(backup_dir, nombre_backup)

                if os.path.exists(db_path):
                    shutil.copy2(db_path, archivo_final)
                    msg = f"Archivo guardado en:\n{archivo_final}"
                    show_message(page, "✅ Copia guardada en el escritorio", "green")
                else:
                    show_message(page, f"❌ No se encuentra DB:\n{db_path}", "red")

            except Exception as ex:
                show_alert("❌ Error General", f"Plataforma: {page.platform}\nError: {str(ex)}", "red")

        # --- DRAWER MANUAL (Custom Stack Implementation) ---
        # Definimos el contenido del drawer
        drawer_content = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text("Digital PyME", size=20, weight="bold", color="white"),
                    bgcolor="#2196F3", padding=20, width=float("inf")
                ),
                ft.ListTile(leading=ft.Icon(ft.Icons.SHOPPING_CART, color="black"), title=ft.Text("Ventas", color="black"), on_click=lambda e: select_drawer_item(0)),
                ft.ListTile(leading=ft.Icon(ft.Icons.LIST_ALT, color="black"), title=ft.Text("Inventario", color="black"), on_click=lambda e: select_drawer_item(1)),
                ft.ListTile(leading=ft.Icon(ft.Icons.DASHBOARD, color="black"), title=ft.Text("Caja", color="black"), on_click=lambda e: select_drawer_item(2)),
                ft.ListTile(leading=ft.Icon(ft.Icons.PEOPLE, color="black"), title=ft.Text("Fiados", color="black"), on_click=lambda e: select_drawer_item(3)),
                ft.ListTile(leading=ft.Icon(ft.Icons.BAR_CHART, color="black"), title=ft.Text("Reportes", color="black"), on_click=lambda e: select_drawer_item(4)),
                ft.ListTile(leading=ft.Icon(ft.Icons.SETTINGS, color="black"), title=ft.Text("Configuración", color="black"), on_click=lambda e: select_drawer_item(5)),
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
            bgcolor=theme_manager.get_color("nav_bg"),
            color="white",
            visible=False,
            actions=[
                ft.IconButton(ft.Icons.LOGOUT, tooltip="Cerrar Caja", on_click=handle_close_turn_global)
            ]
        )
        page.appbar = mobile_appbar
        
        # Estilos de navegación
        _nav_active = ft.ButtonStyle(
            bgcolor=ft.Colors.with_opacity(0.22, "white"),  # fondo blanco suave sobre barra oscura
            color="white",
            overlay_color=ft.Colors.with_opacity(0.15, "white"),
            side=ft.BorderSide(0, "transparent"),
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=14, vertical=8)
        )
        _nav_inactive = ft.ButtonStyle(
            bgcolor="transparent", color=ft.Colors.with_opacity(0.75, "white"),
            overlay_color=ft.Colors.with_opacity(0.18, "white"),
            side=ft.BorderSide(0, "transparent"),
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=14, vertical=8)
        )

        def create_nav_btn(text, icon, idx):
            return ft.TextButton(
                text,
                icon=icon,
                on_click=lambda e: switch_tab(idx),
                style=_nav_active if idx == 0 else _nav_inactive,
            )

        btn_pos      = create_nav_btn("Ventas",         ft.Icons.SHOPPING_CART_OUTLINED,  0)
        btn_inv      = create_nav_btn("Inventario",     ft.Icons.INVENTORY_2_OUTLINED,     1)
        btn_dash     = create_nav_btn("Caja",           ft.Icons.POINT_OF_SALE,            2)
        btn_clients  = create_nav_btn("Fiados",         ft.Icons.PEOPLE_OUTLINE,           3)
        btn_reports  = create_nav_btn("Reportes",       ft.Icons.BAR_CHART_OUTLINED,       4)
        btn_settings = create_nav_btn("Configuración",  ft.Icons.SETTINGS_OUTLINED,        5)
        
        # Contenedor principal
        content_container = ft.Container(
            expand=True,
            padding=10
        )
        
        content_container.content = build_pos_view(page, model, shared_cart=app_state_cart)
        
        # Contenedor para botones de desktop (referencia para ocultar/mostrar)
        top_nav_bar = ft.Container(
            content=ft.Row([
                # Logo / Brand
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text("K", color="white", size=14, weight="bold"),
                            bgcolor=theme_manager.get_color("nav_bg"),
                            width=28, height=28,
                            border_radius=6,
                            alignment=ft.Alignment(0.0, 0.0)
                        ),
                        ft.Text("Digital PyME", color="white", weight="bold", size=14)
                    ], spacing=8),
                    padding=ft.padding.only(right=16)
                ),
                # Divisor vertical
                ft.Container(width=1, height=24, bgcolor="rgba(255,255,255,0.3)"),
                ft.Container(width=4),
                # Tabs de navegación
                ft.Row([btn_pos, btn_inv, btn_dash, btn_clients, btn_reports, btn_settings],
                       spacing=2, scroll=ft.ScrollMode.HIDDEN, expand=True),
                # Acciones globales
                ft.Row([
                    ft.IconButton(
                        ft.Icons.BACKUP_OUTLINED,
                        tooltip="Copia de Seguridad",
                        icon_color="white",
                        icon_size=20,
                        on_click=lambda e: show_backup_dialog(e)
                    ),
                    ft.Container(
                        content=ft.FilledButton(
                            "Cerrar caja",
                            icon=ft.Icons.LOGOUT,
                            style=ft.ButtonStyle(
                                bgcolor=theme_manager.get_color("expense"), color="white",
                                shape=ft.RoundedRectangleBorder(radius=8)
                            ),
                            on_click=handle_close_turn_global
                        ),
                        padding=ft.padding.only(left=8)
                    )
                ], spacing=4)
            ], alignment=ft.MainAxisAlignment.START,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=theme_manager.get_color("nav_bg"),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border=ft.border.only(bottom=ft.border.BorderSide(1, theme_manager.get_color("border")))
        )
        # Banner WiFi (solo visible en modo WiFi)
        wifi_banner = ft.Container(visible=False)
        if is_wifi:
            _local_ip = _get_local_ip()
            wifi_banner = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WIFI, color="white", size=16),
                    ft.Text(f"🌐 Modo WiFi  ·  http://{_local_ip}:{WIFI_PORT}",
                            color="white", size=12, weight="bold"),
                    ft.Container(expand=True),
                    ft.Text(f"Sesión: {page.session_id[:8]}…" if page.session_id else "",
                            color=ft.Colors.with_opacity(0.7, "white"), size=11),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="#1B5E20",
                padding=ft.padding.symmetric(horizontal=16, vertical=6),
            )

        # Layout principal (Columna con botónera y contenido)
        main_layout = ft.Column([
            top_nav_bar,
            wifi_banner,
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
            page.clean()
            page.add(build_activation_view(page, on_success_callback=start_flow))
            return
            
        # 2. Verificar Configuración Inicial (Nombre Negocio)
        biz_name = model.get_config('business_name')
        if not biz_name:
            page.clean()
            page.add(build_setup_view(page, model, on_success_callback=start_flow))
            return

        # 3. Verificar si hay turno abierto (con session_id en modo WiFi)
        _sid = page.data.get('session_id') if isinstance(page.data, dict) else None
        active_shift = model.get_active_turno(session_id=_sid)
        
        if active_shift:
            # SI hay turno, vamos directo a la App
            load_main_app()
        else:
            # NO hay turno, mostramos pantalla de Apertura
            page.clean()  # <--- LIMPIAR ANTES DE MOSTRAR
            page.add(build_shift_view(page, model, on_success_callback=load_main_app))

    # ── Pantalla de PIN WiFi ──────────────────────────────────────
    def show_wifi_pin_screen():
        """Pantalla de autenticación PIN para dispositivos WiFi secundarios."""
        from app.utils.theme import theme_manager
        NAV = theme_manager.get_color("nav_bg")
        PRIMARY = theme_manager.get_color("primary")
        DIM = theme_manager.get_color("text_secondary")
        BORDER = theme_manager.get_color("border")

        pin_value = [""]
        pin_display = ft.Text("● ● ● ●", size=32, weight="bold", color=NAV,
                              text_align=ft.TextAlign.CENTER)
        error_text = ft.Text("", color="#D32F2F", size=13, text_align=ft.TextAlign.CENTER)

        def update_pin_display():
            filled = len(pin_value[0])
            dots = "  ".join(["●" if i < filled else "○" for i in range(4)])
            pin_display.value = dots
            pin_display.update()

        def press_pin_key(key):
            if key == "⌫":
                pin_value[0] = pin_value[0][:-1]
            elif len(pin_value[0]) < 4:
                pin_value[0] += key
                
            update_pin_display()
            error_text.value = ""
            error_text.update()
            
            # Auto-verify when 4 digits are reached
            if len(pin_value[0]) == 4:
                verify_pin()

        def verify_pin(e=None):
            if pin_value[0] == wifi_pin:
                try:
                    page.client_storage.set("pos_authenticated", "1")
                except Exception:
                    pass
                page.clean()
                start_flow()
            else:
                error_text.value = "PIN incorrecto"
                error_text.update()
                pin_value[0] = ""
                update_pin_display()

        KEY_BG = "#e8edf5"
        KEY_DEL = "#fde8e8"

        def mk_key(label):
            if label == "⌫":
                return ft.Container(
                    content=ft.Icon(ft.Icons.BACKSPACE_OUTLINED, color="#D32F2F", size=20),
                    bgcolor=KEY_DEL, border_radius=10,
                    alignment=ft.Alignment(0.0, 0.0),
                    width=90, height=56,
                    on_click=lambda e: press_pin_key("⌫"), ink=True,
                    border=ft.border.all(1, "#f5c6c6")
                )
            if label == "✓":
                return ft.Container(
                    content=ft.Icon(ft.Icons.CHECK, color="white", size=24),
                    bgcolor=PRIMARY, border_radius=10,
                    alignment=ft.Alignment(0.0, 0.0),
                    width=90, height=56,
                    on_click=verify_pin, ink=True,
                )
            return ft.Container(
                content=ft.Text(label, size=22, weight="bold", color=NAV),
                bgcolor=KEY_BG, border_radius=10,
                alignment=ft.Alignment(0.0, 0.0),
                width=90, height=56,
                on_click=lambda e, k=label: press_pin_key(k), ink=True,
                border=ft.border.all(1, "#c8d4e8")
            )

        keypad = ft.Column([
            ft.Row([mk_key("7"), mk_key("8"), mk_key("9")], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([mk_key("4"), mk_key("5"), mk_key("6")], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([mk_key("1"), mk_key("2"), mk_key("3")], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([mk_key("⌫"), mk_key("0"), mk_key("✓")], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=8)

        card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.WIFI_LOCK, size=48, color=PRIMARY),
                ft.Text("Punto de Venta WiFi", size=24, weight="bold", color=NAV),
                ft.Text("Ingrese el PIN de acceso", size=14, color=DIM),
                ft.Container(height=16),
                pin_display,
                error_text,
                ft.Container(height=12),
                keypad,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.CENTER,
               spacing=6, tight=True),
            bgcolor="white",
            padding=ft.padding.symmetric(horizontal=40, vertical=32),
            border_radius=20,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=24,
                                color=ft.Colors.with_opacity(0.12, "black"),
                                offset=ft.Offset(0, 4)),
            border=ft.border.all(1, BORDER),
        )

        page.add(ft.Container(
            content=card,
            alignment=ft.Alignment(0.0, 0.0),
            expand=True,
            bgcolor=theme_manager.get_color("bg_color")
        ))
        page.update()

    # Iniciar flujo (con PIN o recuperando autenticación previa)
    if is_wifi and wifi_pin:
        try:
            is_authenticated = page.client_storage.get("pos_authenticated") == "1"
        except Exception:
            is_authenticated = False
            
        if is_authenticated:
            start_flow()
        else:
            show_wifi_pin_screen()
    else:
        start_flow()

async def main(page: ft.Page):
    try:
        await original_main(page)
    except Exception as e:
        import traceback
        err_trace = traceback.format_exc()
        page.clean()
        page.add(ft.Text(f"Error Crítico en UI:\n{e}\n\n{err_trace}", color="red", selectable=True))
        page.update()

if __name__ == "__main__":
    import sys
    import os
    
    home_dir = os.path.expanduser("~")
    data_dir = os.path.join(home_dir, "Documents", "Digital_PyME")
    if not os.path.exists(data_dir):
        try: os.makedirs(data_dir)
        except OSError: pass
    log_file = os.path.join(data_dir, "crash_log.txt")

    try:
        # Leer configuración WiFi ANTES de iniciar Flet
        wifi_enabled, _ = _read_wifi_config()

        if wifi_enabled:
            # ── Modo WiFi (Servidor Web Multipunto) ──
            # FORZAR A FLET A USAR EL PUERTO SOLICITADO Y MODO WEB EN ENTORNO EMPAQUETADO
            os.environ["FLET_FORCE_WEB_SERVER"] = "true"
            
            local_ip = _get_local_ip()
            print(f"\n{'='*50}")
            print(f"  🌐 MODO WIFI ACTIVADO")
            print(f"  Servidor: http://{local_ip}:{WIFI_PORT}")
            print(f"  Abre esta URL en otro dispositivo")
            print(f"  conectado a la misma red WiFi.")
            print(f"{'='*50}\n")
            
            # Forzar la apertura del navegador localmente (remedio para empaquetados macOS/Windows)
            import threading
            import time
            import webbrowser
            import urllib.request

            def _open_master_browser():
                """Espera a que el servidor Flet esté listo y luego abre el navegador."""
                url = f"http://127.0.0.1:{WIFI_PORT}"
                max_wait = 20  # Máximo 20 segundos de espera
                interval = 0.5
                elapsed = 0

                # Esperar mínimo 2 segundos antes del primer intento
                time.sleep(2)
                elapsed = 2

                while elapsed < max_wait:
                    try:
                        req = urllib.request.urlopen(url, timeout=2)
                        req.close()
                        print(f"  ✅ Servidor listo en {elapsed:.1f}s — abriendo navegador...")
                        break
                    except Exception:
                        time.sleep(interval)
                        elapsed += interval
                else:
                    print(f"  ⚠️ Timeout esperando servidor ({max_wait}s) — intentando abrir navegador de todos modos...")

                # Intentar abrir navegador con webbrowser
                opened = False
                try:
                    opened = webbrowser.open(url)
                except Exception as we:
                    print(f"  webbrowser.open falló: {we}")

                # Fallback: usar subprocess en macOS
                if not opened:
                    try:
                        import subprocess, sys
                        if sys.platform == "darwin":
                            subprocess.Popen(["open", url])
                            print(f"  🔗 Abierto con 'open' (macOS fallback)")
                        elif sys.platform == "win32":
                            subprocess.Popen(["start", url], shell=True)
                            print(f"  🔗 Abierto con 'start' (Windows fallback)")
                    except Exception as se:
                        print(f"  ❌ No se pudo abrir el navegador: {se}")
                        print(f"  👉 Abre manualmente: {url}")

            threading.Thread(target=_open_master_browser, daemon=True).start()

            ft.app(
                target=main,
                view=ft.AppView.WEB_BROWSER,
                host="0.0.0.0",
                port=WIFI_PORT,
                assets_dir="assets"
            )
        else:
            # ── Modo Desktop (ventana nativa) ──
            ft.app(target=main, assets_dir="assets")
            
    except Exception as base_e:
        import traceback
        err = traceback.format_exc()
        try:
            with open(log_file, "a") as f:
                f.write(f"\nCRASH LOG:\n{err}\n")
        except:
            pass
