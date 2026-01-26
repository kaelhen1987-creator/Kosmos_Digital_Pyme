import flet as ft
from app.utils.helpers import is_mobile, show_message

def build_pos_view(page: ft.Page, model, shared_cart=None):
    # Usamos Column en lugar de ListView para que crezcan con el contenido (altura dinámica)
    # y el scroll sea manejado por la página principal (ft.Column scrollable)
    product_list = ft.Column(spacing=10, expand=False) 
    
    # --- ALERTA DE VENCIMIENTO (SnackBar) ---
    last_expiring_count = [0]  # Usar lista para mantener estado mutable
    
    def update_expiration_alert():
        try:
            exp_items = model.get_expiring_products()
            current_count = len(exp_items) if exp_items else 0
            
            # Solo mostrar si hay productos Y el conteo cambió (nuevo o actualizado)
            if current_count > 0 and current_count != last_expiring_count[0]:
                snack = ft.SnackBar(
                    content=ft.Row([
                        ft.Icon(ft.Icons.WARNING_ROUNDED, color="white"),
                        ft.Text(
                            f"⚠️ ATENCIÓN: {current_count} productos próximos a vencer. Revise el Dashboard.",
                            color="white",
                            weight="bold"
                        ),
                    ]),
                    bgcolor="#D32F2F",
                    duration=5000,  # 5 segundos
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
            
            # Actualizar el conteo guardado
            last_expiring_count[0] = current_count
        except Exception as e:
            print(f"Error checking expiration: {e}")

    grid_view = ft.GridView(
        expand=False, # GridView sin expansión forzada
        runs_count=5,
        max_extent=200,
        child_aspect_ratio=0.8,
        spacing=10,
        run_spacing=10,
    )
    cart_list = ft.Column(spacing=5, expand=False)
    
    total_text = ft.Text("Total: $0", size=24, weight="bold", color="white")
    
    # Estado del carrito (Persistente si se pasa shared_cart)
    cart = shared_cart if shared_cart is not None else {}
    current_mode = "scanner" # "scanner" or "visual"
    current_category = "Todas"

    list_container = ft.Container(content=product_list) # Sin expand
    grid_container = ft.Container(content=grid_view, visible=False) # Sin expand
    
    # Toggle de Modo
    def toggle_mode(e):
        nonlocal current_mode
        if current_mode == "scanner":
            current_mode = "visual"
            btn_mode.icon = ft.Icons.LIST
            btn_mode.text = "Modo Lista"
            search_field.visible = False
            category_tabs.visible = True
            list_container.visible = False
            grid_container.visible = True
        else:
            current_mode = "scanner"
            btn_mode.icon = ft.Icons.GRID_VIEW
            btn_mode.text = "Modo Visual"
            search_field.visible = True
            category_tabs.visible = False
            list_container.visible = True
            grid_container.visible = False
        
        refresh_products()
        page.update()

    btn_mode = ft.FilledButton(
        "Modo Visual", 
        icon=ft.Icons.GRID_VIEW, 
        on_click=toggle_mode,
        style=ft.ButtonStyle(bgcolor="#FF9800", color="white")
    )

    # Tabs de Categorías (Solo Visual)
    def filter_category(e):
        nonlocal current_category
        current_category = e.control.data
        refresh_products()

    # Opción: Generaremos los tabs dinámicamente si es posible, o fijos. 
    # Por ahora fijos con los del inventory_view
    cats = ["Todas", "Promociones", "Bebidas", "Cafés", "Sandwiches", "Pastelería", "Almacén", "Cigarros", "Lácteos", "Aseo", "General"]
    category_tabs = ft.Row(
        controls=[
            ft.TextButton(cat, data=cat, on_click=filter_category) for cat in cats
        ],
        scroll=ft.ScrollMode.AUTO,
        visible=False
    )
    
    def handle_barcode_scan(e):
        """Maneja el escaneo de código de barras (Enter automático)"""
        barcode = search_field.value.strip()
        if not barcode:
            return
        
        # Buscar producto por código de barras
        product = model.get_product_by_barcode(barcode)
        
        if product:
            # Producto encontrado: agregar al carrito automáticamente
            product_id = product[0]
            add_to_cart(product_id, product)
            search_field.value = ""  # Limpiar campo para siguiente escaneo
            refresh_products()  # Mostrar todos los productos nuevamente
            search_field.update()
            show_message(page, f"✓ {product[1]} agregado al carrito", "green")
        else:
            # No encontrado por barcode: buscar por nombre (fallback)
            refresh_products(barcode)

    # Campo de búsqueda con soporte para código de barras
    search_field = ft.TextField(
        hint_text="Buscar producto o escanear...",
        on_change=lambda e: refresh_products(e.control.value),
        on_submit=handle_barcode_scan,  # Detecta Enter del lector
        bgcolor="white",
        color="black",
        border_color="#2196F3",
        height=50,
        text_size=16,
        expand=True
    )
    
    def refresh_products(search_query=""):
        products = model.get_all_products()
        
        if current_mode == "scanner":
            # Lógica original de filtro
            # Usamos list_container.content para asegurar referencia
            p_list = list_container.content 
            p_list.controls.clear()
            
            if search_query:
                products = [p for p in products if 
                           search_query.lower() in p[1].lower() or  # Buscar en nombre
                           (len(p) >= 6 and p[5] and search_query.lower() in str(p[5]).lower())]  # Buscar en barcode
            
            if not products:
                 p_list.controls.append(ft.Text("Sin resultados"))
            else:
                 for p in products:
                    # Desempaquetar
                    p_cat = "General"
                    if len(p) >= 7:
                        p_id, p_name, p_price, p_stock, p_crit, p_barcode, p_cat = p[:7]
                    elif len(p) == 6:
                        p_id, p_name, p_price, p_stock, p_crit, p_barcode = p
                    else:
                        p_id, p_name, p_price, p_stock, p_crit = p
                        p_barcode = None
                    
                    stock_color = "green"
                    if p_stock <= p_crit: stock_color = "red"
                    
                    p_list.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text(p_name, size=18, weight="bold", color="#1976D2"),
                                ft.Row([
                                    ft.Text(f"${p_price:,.0f}", size=16, color="#2E7D32", weight="bold"),
                                    ft.Text(f"Stock: {p_stock}", size=14, color=stock_color),
                                ], alignment="spaceBetween")
                            ]),
                            bgcolor="white", padding=15, border_radius=10, border=ft.border.all(1, "grey"),
                            on_click=lambda e, pid=p_id, pinfo=p: add_to_cart(pid, pinfo),
                            ink=True
                        )
                    )
        
        else: # VISUAL MODE (GRID)
            if not grid_container.content:
                 grid_container.content = ft.GridView(expand=True, runs_count=5, max_extent=150, spacing=10, run_spacing=10)
            
            grid = grid_container.content
            grid.controls.clear()
            
            # Filtro por Categoria
            if current_category != "Todas":
                filtered = []
                for p in products:
                    p_cat_val = "General"
                    if len(p) >= 7: p_cat_val = p[6]
                    if not p_cat_val: p_cat_val = "General"
                    
                    if p_cat_val == current_category:
                        filtered.append(p)
                products = filtered

            for p in products:
                # Desempaquetar seguro
                if len(p) >= 7: p_id, p_name, p_price, p_stock, p_crit, p_barcode, p_cat = p[:7]
                elif len(p) == 6: p_id, p_name, p_price, p_stock, p_crit, p_barcode = p
                else: p_id, p_name, p_price, p_stock, p_crit = p
                
                stock_color = "white"
                bg_card = "#2196F3" # Blue default
                if p_stock <= p_crit: bg_card = "#F44336" # Red alert
                
                grid.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(p_name, size=14, weight="bold", color="white", text_align="center", no_wrap=False),
                            ft.Text(f"${p_price:,.0f}", size=12, color="white", weight="bold"),
                        ], alignment="center", horizontal_alignment="center"),
                        bgcolor=bg_card,
                        padding=10,
                        border_radius=8,
                        alignment=ft.Alignment(0, 0),
                        on_click=lambda e, pid=p_id, pinfo=p: add_to_cart(pid, pinfo),
                        ink=True
                    )
                )
        if page: 
            page.update()
            update_expiration_alert()
    
    def refresh_cart():
        cart_list.controls.clear()
        total = 0
        
        if not cart:
            cart_list.controls.append(
                ft.Text("Carrito vacío\nClick en productos para agregar", 
                      size=14, color="grey", text_align="center")
            )
        else:
            for pid, item in cart.items():
                info = item['info']
                qty = item['qty']
                subtotal = info[2] * qty
                total += subtotal
                
                cart_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(info[1], size=14, color="black", weight="bold"),
                                ft.Text(f"${info[2]:,.0f} x {qty}", size=12, color="grey"),
                            ], expand=True, spacing=2),
                            ft.Text(f"${subtotal:,.0f}", size=14, color="green", weight="bold"),
                            ft.TextButton(
                                "Eliminar",
                                on_click=lambda e, p=pid: remove_from_cart(p),
                                style=ft.ButtonStyle(color="red"),
                            )
                        ], alignment="center"),
                        bgcolor="white",
                        padding=10,
                        border_radius=5,
                        border=ft.border.all(1, "#e0e0e0"),
                    )
                )
        
        total_text.value = f"Total: ${total:,.0f}"
        page.update()
    
    def add_to_cart(product_id, product_info):
        if product_id not in cart:
            cart[product_id] = {'info': product_info, 'qty': 0}
        cart[product_id]['qty'] += 1
        
        if cart[product_id]['qty'] > product_info[3]:
            cart[product_id]['qty'] -= 1
            show_message(page, "Stock insuficiente", "red")
            return
        
        refresh_cart()
        show_message(page, f"{product_info[1]} agregado", "green")
    
    def remove_from_cart(product_id):
        if product_id in cart:
            del cart[product_id]
        refresh_cart()
    
    def checkout(e):
        if not cart:
            show_message(page, "El carrito está vacío", "orange")
            return
            
        def finalize_sale(payment_type, client_id=None):
            try:
                # 1. Registrar venta física (baja de stock)
                # Pasamos el medio_pago seleccionado. Si es DEUDA, igual se guarda como tal.
                venta_id = model.register_sale(cart, medio_pago=payment_type)
                
                # 2. Si es FIADO, registrar deuda
                if payment_type == 'DEUDA' and client_id:
                    total_amount = sum(item['qty'] * item['info'][2] for item in cart.values())
                    model.add_movement(client_id, 'DEUDA', total_amount, f"Compra #{venta_id} (Fiado)", venta_id)
                
                # 3. Limpiar y refrescar
                cart.clear()
                refresh_cart()
                refresh_products()
                
                dlg_payment.open = False
                page.update()
                
                msg = f"Venta #{venta_id} exitosa"
                if payment_type == 'DEUDA':
                    msg += " (Registrada en Cuaderno)"
                show_message(page, msg, "green")
                
            except Exception as ex:
                show_message(page, f"Error: {str(ex)}", "red")

        # --- Dialogo de Selección de Cliente (Para Fiado) ---
        def show_client_selector(e=None, preselect_id=None):
            clients = model.get_clients_with_balance()
            client_list = ft.ListView(expand=True, height=300)
            
            def finalize_with_client(client_data):
                # Calcular total venta
                current_total = sum(item['qty'] * item['info'][2] for item in cart.values())
                
                # Verificar Limite de Credito
                # client_data keys: id, nombre, telefono, alias, limite, deuda_total, pagado_total, saldo_actual
                limit = client_data.get('limite', 0)
                current_balance = client_data.get('saldo_actual', 0)
                
                if limit > 0:
                    new_balance = current_balance + current_total
                    if new_balance > limit:
                        # Bloquear venta
                        def close_alert(e):
                            dlg_limit.open = False
                            page.update()
                            
                        dlg_limit = ft.AlertDialog(
                            title=ft.Text("Límite de Crédito Excedido", color="red"),
                            content=ft.Column([
                                ft.Text(f"El cliente {client_data['nombre']} tiene un límite de ${limit:,.0f}."),
                                ft.Text(f"Deuda Actual: ${current_balance:,.0f}"),
                                ft.Text(f"Esta Compra: ${current_total:,.0f}"),
                                ft.Divider(),
                                ft.Text(f"Nuevo Saldo: ${new_balance:,.0f}", weight="bold"),
                                ft.Text("No se puede fiar esta venta.", color="red"),
                            ], tight=True),
                            actions=[ft.TextButton("Entendido", on_click=close_alert)]
                        )
                        page.overlay.append(dlg_limit)
                        dlg_limit.open = True
                        page.update()
                        return

                # Si pasa validación, procesar
                finalize_sale('DEUDA', client_id=client_data['id'])

            def render_list(search_term="", update_ui=True):
                client_list.controls.clear()
                
                filtered_clients = clients
                if search_term:
                    filtered_clients = [c for c in clients if search_term.lower() in c['nombre'].lower()]

                if not filtered_clients:
                    msg = "No se encontraron clientes." if clients else "No hay clientes registrados."
                    client_list.controls.append(ft.Text(msg, color="grey"))
                
                for c in filtered_clients:
                    client_list.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.PERSON),
                            title=ft.Text(c['nombre']),
                            subtitle=ft.Text(f"Deuda: ${c['saldo_actual']:,.0f} | Límite: {'$' + format(c['limite'], ',.0f') if c['limite'] > 0 else '∞'}"),
                            on_click=lambda e, cl=c: finalize_with_client(cl)
                        )
                    )
                if update_ui and client_list.page:
                    client_list.update()

            def show_add_client_form(e):
                name_field = ft.TextField(label="Nombre Completo", autofocus=True)
                phone_field = ft.TextField(label="Teléfono (Opcional)")
                limit_field = ft.TextField(label="Límite de Crédito ($)", value="0", keyboard_type=ft.KeyboardType.NUMBER, suffix=ft.Text("(0 = Sin límite)"))
                
                def save_new_client(e):
                    if not name_field.value:
                        name_field.error_text = "Requerido"
                        name_field.update()
                        return
                        
                    try:
                        limit_val = float(limit_field.value) if limit_field.value else 0
                        new_id = model.add_client(name_field.value, phone_field.value or "", "", limit_val)
                        show_message(page, "Cliente creado correctamente", "green")
                        # Recargar lista volviedo a llamar al selector
                        show_client_selector(preselect_id=new_id)
                    except Exception as ex:
                         show_message(page, f"Error: {ex}", "red")

                dlg_payment.title = ft.Text("Nuevo Cliente")
                dlg_payment.content = ft.Column([
                    ft.Text("Ingresa los datos del cliente para fiado:"),
                    name_field,
                    phone_field,
                    limit_field,
                    ft.Container(height=10),
                    ft.FilledButton("Guardar Cliente", on_click=save_new_client, width=float("inf"))
                ], tight=True, width=300)
                
                dlg_payment.actions = [
                    ft.TextButton("Volver", on_click=lambda e: show_client_selector())
                ]
                page.update()

            search_field = ft.TextField(
                hint_text="Buscar cliente...",
                on_change=lambda e: render_list(e.control.value, update_ui=True),
                autofocus=True,
                prefix_icon=ft.Icons.SEARCH,
                expand=True
            )
            
            btn_add_client = ft.IconButton(
                ft.Icons.PERSON_ADD, 
                tooltip="Crear Nuevo Cliente", 
                icon_color="green",
                on_click=show_add_client_form
            )

            # Render inicial (Sin update para evitar error)
            render_list(update_ui=False)
            
            dlg_payment.title = ft.Text("Selecciona Cliente")
            dlg_payment.content = ft.Column([
                ft.Row([search_field, btn_add_client], alignment="center"),
                client_list
            ], height=400, width=300)
            
            dlg_payment.actions = [ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_payment))]
            page.update()

        # --- Dialogo de Pago en Efectivo (Calculo de Vuelto) ---
        def show_cash_dialog(total_amount):
            
            txt_pago = ft.TextField(
                label="Monto Entregado ($)", 
                keyboard_type=ft.KeyboardType.NUMBER,
                autofocus=True,
                text_size=20
            )
            txt_vuelto = ft.Text("Vuelto: $0", size=20, weight="bold", color="grey")
            
            def calculate_change(e):
                try:
                    pago = int(txt_pago.value) if txt_pago.value else 0
                    vuelto = pago - total_amount
                    
                    if vuelto >= 0:
                        txt_vuelto.value = f"Vuelto: ${vuelto:,.0f}"
                        txt_vuelto.color = "green"
                        btn_confirm_cash.disabled = False
                    else:
                        txt_vuelto.value = f"Faltan: ${abs(vuelto):,.0f}"
                        txt_vuelto.color = "red"
                        btn_confirm_cash.disabled = True
                    
                    dlg_cash.update()
                except ValueError:
                    pass

            txt_pago.on_change = calculate_change

            def confirm_cash_payment(e):
                dlg_cash.open = False
                finalize_sale('EFECTIVO')

            btn_confirm_cash = ft.ElevatedButton(
                "Confirmar Venta", 
                bgcolor="green", color="white", 
                disabled=True,
                on_click=confirm_cash_payment
            )

            dlg_cash = ft.AlertDialog(
                title=ft.Text("Pago en Efectivo"),
                content=ft.Column([
                    ft.Text(f"Total a Pagar: ${total_amount:,.0f}", size=24, weight="bold"),
                    ft.Divider(),
                    txt_pago,
                    txt_vuelto
                ], height=200, tight=True),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_cash_dialog(e)),
                    btn_confirm_cash
                ]
            )
            
            def close_cash_dialog(e):
                dlg_cash.open = False
                page.update()

            page.overlay.append(dlg_cash)
            dlg_cash.open = True
            page.update()

        # --- Dialogo Principal de Pago ---
        
        def pay_with(method):
            if method == "EFECTIVO":
                show_cash_dialog(sum(item['qty'] * item['info'][2] for item in cart.values()))
            elif method == "FIADO":
                show_client_selector()
            else:
                # TRANSFERENCIA, DEBITO, CREDITO -> CONFIRMACIÓN
                total = sum(item['qty'] * item['info'][2] for item in cart.values())
                
                def confirm_fast_payment(e):
                    dlg_confirm.open = False
                    finalize_sale(method)
                    
                def close_confirm(e):
                    dlg_confirm.open = False
                    page.update()
                    
                dlg_confirm = ft.AlertDialog(
                    title=ft.Text("Confirmar Pago"),
                    content=ft.Column([
                        ft.Text(f"¿Registrar pago con {method}?", size=18),
                        ft.Text(f"Monto: ${total:,.0f}", weight="bold", size=20, color="green"),
                    ], tight=True, height=100),
                    actions=[
                        ft.TextButton("Cancelar", on_click=close_confirm, style=ft.ButtonStyle(color="red")),
                        ft.FilledButton("Confirmar", on_click=confirm_fast_payment, style=ft.ButtonStyle(bgcolor="green"))
                    ],
                    actions_alignment=ft.MainAxisAlignment.END
                )
                page.overlay.append(dlg_confirm)
                dlg_confirm.open = True
                page.update()

        btn_style = ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5), color="white")

        dlg_payment = ft.AlertDialog(
            title=ft.Text("Método de Pago"),
            content=ft.Column([
                ft.Row([
                    ft.FilledButton(
                        "Efectivo", icon=ft.Icons.MONEY, 
                        style=ft.ButtonStyle(bgcolor="green", color="white", shape=ft.RoundedRectangleBorder(radius=5)),
                        on_click=lambda e: pay_with("EFECTIVO"), expand=True, height=50
                    ),
                    ft.FilledButton(
                        "Fiado", icon=ft.Icons.BOOK, 
                        style=ft.ButtonStyle(bgcolor="red", color="white", shape=ft.RoundedRectangleBorder(radius=5)),
                        on_click=lambda e: pay_with("FIADO"), expand=True, height=50
                    ),
                ]),
                ft.Divider(),
                ft.Text("Tarjetas y Bancos:", size=12, color="grey"),
                ft.Row([
                    ft.FilledButton("Transferencia", icon=ft.Icons.QR_CODE, style=ft.ButtonStyle(bgcolor="#1976D2", color="white"), on_click=lambda e: pay_with("TRANSFERENCIA"), expand=True),
                    ft.FilledButton("Débito", icon=ft.Icons.CREDIT_CARD, style=ft.ButtonStyle(bgcolor="#1976D2", color="white"), on_click=lambda e: pay_with("DEBITO"), expand=True),
                    ft.FilledButton("Crédito", icon=ft.Icons.CREDIT_CARD, style=ft.ButtonStyle(bgcolor="#1976D2", color="white"), on_click=lambda e: pay_with("CREDITO"), expand=True),
                ]),
            ], tight=True, width=500),
        )

        def close_dialog(dlg):
            dlg.open = False
            page.update()

        page.overlay.append(dlg_payment)
        dlg_payment.open = True
        page.update()
    
    refresh_products()
    refresh_cart()
    
    # Layout Responsive Robusto con ResponsiveRow
    layout = ft.ResponsiveRow([
        # 1. Carrito (Primero en el código = Arriba en móvil / Izquierda en desktop)
        ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text("CARRITO", size=24, weight="bold", color="white"),
                        total_text
                    ], alignment="center", horizontal_alignment="center", spacing=5),
                    bgcolor="#4CAF50",
                    padding=15,
                    border_radius=ft.border_radius.only(top_left=10, top_right=10),
                ),
                ft.Container(
                    content=cart_list,
                    height=None, # Altura dinámica (crece con items), scroll manejado por pagina
                    padding=5,
                ),
                ft.Divider(height=1, color="grey"),
                ft.Container(
                    content=ft.Column([
                        ft.FilledButton(
                            "COBRAR",
                            on_click=checkout,
                            style=ft.ButtonStyle(bgcolor="#4CAF50", color="white"),
                            height=50,
                            width=None, # Ancho automático
                            expand=True, # Expandir en ancho
                        ),
                    ], spacing=10, horizontal_alignment="center"),
                    padding=10,
                ),
            ], spacing=0),
            bgcolor="white",
            border_radius=10,
            border=ft.border.all(1, "#e0e0e0"),
            col={"xs": 12, "md": 4}, # 12 columnas en móvil, 4 en desktop
        ),

        # 2. Productos (Segundo en el código = Abajo en móvil / Derecha en desktop)
        ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Text("PRODUCTOS", size=20, weight="bold", color="white"),
                        btn_mode
                    ], alignment="space_between"),
                    bgcolor="#2196F3",
                    padding=15,
                    border_radius=ft.border_radius.only(top_left=10, top_right=10),
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Row([search_field]),
                        category_tabs
                    ], spacing=10),
                    padding=10,
                    bgcolor="white",
                ),
                ft.Container(
                    content=ft.Column([list_container, grid_container]),
                    height=None, # Altura dinámica
                    padding=10
                ),
            ], spacing=0),
            bgcolor="white",
            border_radius=10,
            border=ft.border.all(1, "#e0e0e0"),
            col={"xs": 12, "md": 8}, # 12 columnas en móvil, 8 en desktop
        ),
    ], spacing=10)

    # Envolver en Columna Scrollable para permitir scroll de pagina en movil
    # FIX: Scanner es global ahora, no local.
    return ft.Column([layout], scroll=ft.ScrollMode.AUTO, expand=True)
