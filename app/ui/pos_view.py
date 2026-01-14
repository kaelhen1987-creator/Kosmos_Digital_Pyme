import flet as ft
from app.utils.helpers import is_mobile, show_message

def build_pos_view(page: ft.Page, model):
    product_list = ft.ListView(spacing=10, padding=10, expand=True)
    cart_list = ft.ListView(spacing=5, padding=10, expand=True)
    total_text = ft.Text("Total: $0", size=24, weight="bold", color="black")
    
    # Estado local del carrito
    cart = {}

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
        product_list.controls.clear()
        products = model.get_all_products()
        
        # Filtrar por búsqueda (nombre o código de barras)
        if search_query:
            products = [p for p in products if 
                       search_query.lower() in p[1].lower() or  # Buscar en nombre
                       (len(p) >= 6 and p[5] and search_query.lower() in str(p[5]).lower())]  # Buscar en barcode
        
        if not products:
            product_list.controls.append(
                ft.Container(
                    content=ft.Text("No hay productos.\nVe a Inventario para agregar.", 
                                  size=16, color="black", text_align="center"),
                    bgcolor="#fff3cd",
                    padding=30,
                    border_radius=10,
                )
            )
        else:
            for p in products:
                # Desempaquetar producto (ahora incluye codigo_barras)
                if len(p) >= 6:
                    p_id, p_name, p_price, p_stock, p_crit, p_barcode = p
                else:
                    p_id, p_name, p_price, p_stock, p_crit = p
                    p_barcode = None
                
                stock_color = "green"
                if p_stock <= p_crit:
                    stock_color = "red"
                elif p_stock <= p_crit + 5:
                    stock_color = "orange"
                
                product_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(p_name, size=18, weight="bold", color="#1976D2"),
                            ft.Container(height=5),  # Espaciado
                            ft.Row([
                                ft.Text("Precio:", size=14, color="#666666", weight="w500"),
                                ft.Text(f"${p_price:,.0f}", size=16, color="#2E7D32", weight="bold"),
                            ], spacing=5),
                            ft.Row([
                                ft.Text("Stock:", size=14, color="#666666", weight="w500"),
                                ft.Text(f"{p_stock}", size=16, color=stock_color, weight="bold"),
                            ], spacing=5),
                        ], spacing=3),
                        bgcolor="white",
                        padding=15,
                        border_radius=10,
                        border=ft.border.all(2, "#2196F3"),
                        on_click=lambda e, pid=p_id, pinfo=p: add_to_cart(pid, pinfo),
                        ink=True,
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=4,
                            color=ft.Colors.with_opacity(0.1, "black"),
                            offset=ft.Offset(0, 2),
                        )
                    )
                )
        page.update()
    
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
        
        try:
            # Registrar venta completa (Cabecera + Detalles + Descuento Stock)
            venta_id = model.register_sale(cart)
            
            cart.clear()
            refresh_cart()
            refresh_products()
            show_message(page, f"Venta #{venta_id} exitosa", "green")
        except Exception as ex:
            show_message(page, f"Error al procesar venta: {str(ex)}", "red")
    
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
                    # Altura dinámica: se ajusta al contenido
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
                    content=ft.Text("PRODUCTOS", size=20, weight="bold", color="white"),
                    bgcolor="#2196F3",
                    padding=15,
                    border_radius=ft.border_radius.only(top_left=10, top_right=10),
                ),
                ft.Container(
                    content=search_field,
                    padding=10,
                    bgcolor="white",
                ),
                ft.Container(
                    content=product_list,
                    height=400 if is_mobile(page) else 600,
                ),
            ], spacing=0),
            bgcolor="white",
            border_radius=10,
            border=ft.border.all(1, "#e0e0e0"),
            col={"xs": 12, "md": 8}, # 12 columnas en móvil, 8 en desktop
        ),
    ], spacing=10)
