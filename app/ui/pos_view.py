import flet as ft
from app.utils.helpers import is_mobile, show_message

def build_pos_view(page: ft.Page, model, shared_cart=None):
    product_list = ft.ListView(spacing=10, padding=10, expand=True)
    cart_list = ft.ListView(spacing=5, padding=10, expand=True)
    total_text = ft.Text("Total: $0", size=24, weight="bold", color="black")
    
    # Estado del carrito (Persistente si se pasa shared_cart)
    cart = shared_cart if shared_cart is not None else {}
    current_mode = "scanner" # "scanner" or "visual"
    current_category = "Todas"

    list_container = ft.Container(content=product_list, expand=True) # Contenedor para vista lista
    grid_container = ft.Container(expand=True, visible=False) # Contenedor para vista grilla
    
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
            btn_mode.icon = ft.Icons.grid_view
            btn_mode.text = "Modo Visual"
            search_field.visible = True
            category_tabs.visible = False
            list_container.visible = True
            grid_container.visible = False
        
        refresh_products()
        page.update()

    btn_mode = ft.ElevatedButton(
        "Modo Visual", 
        icon=ft.Icons.GRID_VIEW, 
        on_click=toggle_mode,
        bgcolor="#FF9800", color="white"
    )

    # Tabs de Categorías (Solo Visual)
    def filter_category(e):
        nonlocal current_category
        current_category = e.control.data
        refresh_products()

    # Opción: Generaremos los tabs dinámicamente si es posible, o fijos. 
    # Por ahora fijos con los del inventory_view
    cats = ["Todas", "Bebidas", "Cafés", "Sandwiches", "Pastelería", "Almacén", "Cigarros", "Lácteos", "Aseo", "General"]
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
        hint_text="Buscar producto o escanear código de barras...",
        on_change=lambda e: refresh_products(e.control.value),
        on_submit=handle_barcode_scan,  # Detecta Enter del lector
        bgcolor="white",
        color="black",
        border_color="#2196F3",
        height=50,
        text_size=16,
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
                        p_id, p_name, p_price, p_stock, p_crit, p_barcode, p_cat = p
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
                if len(p) >= 7: p_id, p_name, p_price, p_stock, p_crit, p_barcode, p_cat = p
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
        if page: page.update()
    
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
                venta_id = model.register_sale(cart)
                
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
        def show_client_selector(e):
            clients = model.get_clients_with_balance()
            client_list = ft.ListView(expand=True, height=300)
            
            def finalize_with_client(c_id):
                finalize_sale('DEUDA', client_id=c_id)

            def render_list(search_term="", update_ui=True):
                client_list.controls.clear()
                
                filtered_clients = clients
                if search_term:
                    filtered_clients = [c for c in clients if search_term.lower() in c['nombre'].lower()]

                if not filtered_clients:
                    msg = "No se encontraron clientes." if clients else "No hay clientes registrados. Ve a 'Cuaderno' para crear uno."
                    client_list.controls.append(ft.Text(msg, color="grey"))
                
                for c in filtered_clients:
                    client_list.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.PERSON),
                            title=ft.Text(c['nombre']),
                            subtitle=ft.Text(f"Deuda: ${c['saldo_actual']:,.0f}"),
                            on_click=lambda e, cid=c['id']: finalize_with_client(cid)
                        )
                    )
                if update_ui and client_list.page:
                    client_list.update()

            search_field = ft.TextField(
                hint_text="Buscar cliente...",
                on_change=lambda e: render_list(e.control.value, update_ui=True),
                autofocus=True,
                prefix_icon=ft.Icons.SEARCH
            )
            
            # Render inicial (Sin update para evitar error)
            render_list(update_ui=False)
            
            dlg_payment.title = ft.Text("Selecciona Cliente")
            dlg_payment.content = ft.Column([
                search_field,
                client_list
            ], height=400, width=300)
            
            dlg_payment.actions = [ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_payment))]
            page.update()

        # --- Dialogo Principal de Pago ---
        dlg_payment = ft.AlertDialog(
            title=ft.Text("Método de Pago"),
            content=ft.Row([
                ft.ElevatedButton(
                    "Efectivo / Transf", # Texto acortado para móvil
                    icon="money", 
                    style=ft.ButtonStyle(bgcolor="green", color="white", shape=ft.RoundedRectangleBorder(radius=5)),
                    on_click=lambda e: finalize_sale('EFECTIVO'),
                    height=60,
                    expand=True
                ),
                ft.ElevatedButton(
                    "Fiado / Cuenta", 
                    icon="book", 
                    style=ft.ButtonStyle(bgcolor="red", color="white", shape=ft.RoundedRectangleBorder(radius=5)),
                    on_click=show_client_selector,
                    height=60,
                    expand=True
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
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
    return ft.ResponsiveRow([
        # 1. Carrito (Primero en el código = Arriba en móvil / Izquierda en desktop)
        ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Text("CARRITO", size=20, weight="bold", color="white"),
                        total_text
                    ], alignment="space_between"),
                    bgcolor="#4CAF50",
                    padding=15,
                    border_radius=ft.border_radius.only(top_left=10, top_right=10),
                ),
                ft.Container(
                    content=cart_list,
                    # Altura dinámica
                    padding=5,
                ),
                ft.Divider(height=1, color="grey"),
                ft.Container(
                    content=ft.Column([
                        ft.ElevatedButton(
                            "COBRAR",
                            on_click=checkout,
                            bgcolor="#4CAF50",
                            color="white",
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
                    content=ft.Column([search_field, category_tabs]),
                    padding=10,
                    bgcolor="white",
                ),
                ft.Container(
                    content=ft.Stack([list_container, grid_container]),
                    height=400 if is_mobile(page) else 600,
                    padding=10
                ),
            ], spacing=0),
            bgcolor="white",
            border_radius=10,
            border=ft.border.all(1, "#e0e0e0"),
            col={"xs": 12, "md": 8}, # 12 columnas en móvil, 8 en desktop
        ),
    ], spacing=10)
