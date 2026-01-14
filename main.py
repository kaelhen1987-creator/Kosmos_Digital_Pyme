#!/opt/homebrew/bin/python3
import flet as ft
import sqlite3

# =============================================================================
# MODELO (MODEL) - LOGICA PURA
# =============================================================================
class InventarioModel:
    def __init__(self, db_name='inventario.db'):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                precio REAL NOT NULL,
                stock INTEGER NOT NULL,
                stock_critico INTEGER NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def get_all_products(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos")
        res = cursor.fetchall()
        conn.close()
        return res

    def add_product(self, nombre, precio, stock, stock_critico):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO productos (nombre, precio, stock, stock_critico) VALUES (?, ?, ?, ?)",
                           (nombre, precio, stock, stock_critico))
            conn.commit()
            return True
        finally:
            conn.close()

    def increase_stock_by_name(self, nombre, cantidad):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET stock = stock + ? WHERE nombre = ?", (cantidad, nombre))
        conn.commit()
        conn.close()

    def increase_stock_by_id(self, product_id, cantidad):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (cantidad, product_id))
        conn.commit()
        conn.close()

    def update_product(self, product_id, nombre, precio, stock, stock_critico):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET nombre = ?, precio = ?, stock = ?, stock_critico = ? WHERE id = ?",
                       (nombre, precio, stock, stock_critico, product_id))
        conn.commit()
        conn.close()

    def delete_product(self, product_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM productos WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()

    def decrease_stock(self, product_id, quantity=1):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (quantity, product_id))
        conn.commit()
        conn.close()


# =============================================================================
# VISTA (FLET UI)
# =============================================================================
def main(page: ft.Page):
    page.title = "SOS Digital PyME - POS"
    page.bgcolor = "#f5f5f5"
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    
    # Configuración responsive
    page.window.min_width = 350
    page.window.min_height = 600
    
    model = InventarioModel()
    cart = {}
    current_view = ft.Ref[ft.Container]()
    current_tab_index = {"index": 0}
    
    # Detectar si es móvil por el ancho
    def is_mobile():
        if page.window.width:
            return page.window.width < 600
        return False
    
    def show_message(msg, color="blue"):
        snack = ft.SnackBar(ft.Text(msg, color="white"), bgcolor=color, open=True)
        page.overlay.append(snack)
        page.update()
    
    # ========== VISTA POS CON CARRITO ==========
    def build_pos_view():
        product_list = ft.ListView(spacing=10, padding=10, expand=True)
        cart_list = ft.ListView(spacing=5, padding=10, expand=True)
        total_text = ft.Text("Total: $0", size=24, weight="bold", color="black")
        
        # Campo de búsqueda
        search_field = ft.TextField(
            hint_text="🔍 Buscar producto...",
            on_change=lambda e: refresh_products(e.control.value),
            bgcolor="white",
            color="black",
            border_color="#2196F3",
            height=50,
            text_size=16,
        )
        
        def refresh_products(search_query=""):
            product_list.controls.clear()
            products = model.get_all_products()
            
            # Filtrar por búsqueda
            if search_query:
                products = [p for p in products if search_query.lower() in p[1].lower()]
            
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
                    p_id, p_name, p_price, p_stock, p_crit = p
                    
                    stock_color = "green"
                    if p_stock <= p_crit:
                        stock_color = "red"
                    elif p_stock <= p_crit + 5:
                        stock_color = "orange"
                    
                    product_list.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text(p_name, size=20, weight="bold", color="black"),
                                ft.Text(f"Precio: ${p_price:,.0f}", size=18, color="green", weight="bold"),
                                ft.Text(f"Stock: {p_stock}", size=16, color=stock_color, weight="bold"),
                                ft.Text("👆 Click para agregar al carrito", size=12, color="grey", italic=True),
                            ], spacing=5),
                            bgcolor="white",
                            padding=20,
                            border_radius=10,
                            border=ft.border.all(3, "#2196F3"),
                            on_click=lambda e, pid=p_id, pinfo=p: add_to_cart(pid, pinfo),
                            ink=True,
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
                                    "🗑️",
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
                show_message("¡Stock insuficiente!", "red")
                return
            
            refresh_cart()
            show_message(f"✓ {product_info[1]} agregado", "green")
        
        def remove_from_cart(product_id):
            if product_id in cart:
                del cart[product_id]
            refresh_cart()
        
        def checkout(e):
            if not cart:
                show_message("El carrito está vacío", "orange")
                return
            
            for pid, item in cart.items():
                model.decrease_stock(pid, item['qty'])
            
            cart.clear()
            refresh_cart()
            refresh_products()
            show_message("¡Venta exitosa! ✓", "green")
        
        refresh_products()
        refresh_cart()
        
        # Layout Responsive Robusto con ResponsiveRow
        return ft.ResponsiveRow([
            # 1. Carrito (Primero en el código = Arriba en móvil / Izquierda en desktop)
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Text("🛒 CARRITO", size=20, weight="bold", color="white"),
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
            # Nota: En ResponsiveRow el orden visual sigue el orden del código.
            # Al poner el carrito primero, en desktop quedará a la izquierda.
            
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
                        height=400 if is_mobile() else 600,
                    ),
                ], spacing=0),
                bgcolor="white",
                border_radius=10,
                border=ft.border.all(1, "#e0e0e0"),
                col={"xs": 12, "md": 8}, # 12 columnas en móvil, 8 en desktop
            ),
        ], spacing=10)
    
    # ========== VISTA INVENTARIO ==========
    def build_inventory_view():
        name_field = ft.TextField(
            label="Nombre del Producto",
            bgcolor="white",
            color="black",
            border_color="#2196F3",
            hint_text="Ej: Coca-Cola 2L",
            expand=True,
            filled=True,
            border_width=2,
        )
        price_field = ft.TextField(
            label="Precio sin IVA",
            bgcolor="white",
            color="black",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color="#2196F3",
            hint_text="1000",
            on_change=lambda e: update_price_preview(),
            filled=True,
            border_width=2,
            expand=1,
        )
        stock_field = ft.TextField(
            label="Stock Inicial",
            bgcolor="white",
            color="black",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color="#2196F3",
            hint_text="50",
            filled=True,
            border_width=2,
            expand=1,
        )
        critic_field = ft.TextField(
            label="Stock Crítico",
            bgcolor="white",
            color="black",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color="#2196F3",
            hint_text="5",
            filled=True,
            border_width=2,
            expand=1,
        )
        
        # Preview del precio con IVA
        price_preview = ft.Text(
            "Precio con IVA (19%): $0",
            size=14,
            color="green",
            weight="bold",
        )
        
        def update_price_preview():
            try:
                if price_field.value:
                    precio_sin_iva = float(price_field.value)
                    precio_con_iva = precio_sin_iva * 1.19
                    price_preview.value = f"💵 Precio con IVA (19%): ${precio_con_iva:,.0f}"
                else:
                    price_preview.value = "Precio con IVA (19%): $0"
                price_preview.update()
            except ValueError:
                price_preview.value = "Precio con IVA (19%): $0"
                price_preview.update()
        
        product_list = ft.ListView(spacing=10, padding=10, expand=True)
        
        # Campo de búsqueda para inventario
        search_inventory = ft.TextField(
            hint_text="🔍 Buscar en inventario...",
            on_change=lambda e: refresh_products(e.control.value),
            bgcolor="white",
            color="black",
            border_color="#2196F3",
            height=50,
            text_size=16,
            expand=True,  # Se expande para ocupar todo el ancho
        )
        
        def refresh_products(search_query=""):
            product_list.controls.clear()
            products = model.get_all_products()
            
            # Filtrar por búsqueda
            if search_query:
                products = [p for p in products if search_query.lower() in p[1].lower()]
            
            if not products:
                product_list.controls.append(
                    ft.Container(
                        content=ft.Text(
                            "📦 No hay productos registrados\n\n👆 Usa el formulario arriba para agregar productos",
                            size=16,
                            color="grey",
                            text_align="center"
                        ),
                        padding=40,
                    )
                )
            else:
                for p in products:
                    p_id, p_name, p_price, p_stock, p_crit = p
                    
                    bg_color = "white"
                    status_emoji = "✅"
                    if p_stock <= p_crit:
                        bg_color = "#ffcccc"
                        status_emoji = "⚠️"
                    elif p_stock <= p_crit + 5:
                        bg_color = "#fff9c4"
                        status_emoji = "⚡"
                    
                    product_list.controls.append(
                        ft.Container(
                            content=ft.Column([
                                # Fila 1: Nombre del producto con emoji de estado
                                ft.Row([
                                    ft.Text(
                                        f"{status_emoji} {p_name}", 
                                        size=18, 
                                        weight="bold", 
                                        color="black"
                                    ),
                                ]),
                                # Fila 2: Info y botones
                                ft.Row([
                                    # Columna izquierda: Datos del producto
                                    ft.Column([
                                        ft.Row([
                                            ft.Text("💰", size=14),
                                            ft.Text(f"${p_price:,.0f}", size=14, color="black", weight="bold"),
                                        ], spacing=5),
                                        ft.Row([
                                            ft.Text("📦", size=14),
                                            ft.Text(f"Stock: {p_stock}", size=14, color="black"),
                                        ], spacing=5),
                                        ft.Row([
                                            ft.Text("🔔", size=14),
                                            ft.Text(f"Crítico: {p_crit}", size=14, color="black"),
                                        ], spacing=5),
                                    ], spacing=3, expand=True),
                                    # Columna derecha: Botones de acción (todos verticales)
                                    ft.Column([
                                        ft.TextButton(
                                            "➕ Stock",
                                            on_click=lambda e, pid=p_id: open_add_stock_dialog(pid),
                                            style=ft.ButtonStyle(color="blue"),
                                        ),
                                        ft.TextButton(
                                            "✏️ Editar",
                                            on_click=lambda e, pid=p_id, pdata=p: open_edit_dialog(pid, pdata),
                                            style=ft.ButtonStyle(color="orange"),
                                        ),
                                        ft.TextButton(
                                            "🗑️ Eliminar",
                                            on_click=lambda e, pid=p_id: delete_product(pid),
                                            style=ft.ButtonStyle(color="red"),
                                        ),
                                    ], spacing=5, horizontal_alignment="end"),
                                ], alignment="spaceBetween"),
                            ], spacing=10),
                            bgcolor=bg_color,
                            padding=15,
                            border_radius=10,
                            border=ft.border.all(2, "grey"),
                        )
                    )
            page.update()
        
        def add_product(e):
            try:
                nombre = name_field.value.strip()
                if not nombre:
                    show_message("⚠️ Ingresa el nombre del producto", "orange")
                    return
                
                precio_sin_iva = float(price_field.value)
                stock = int(stock_field.value)
                critico = int(critic_field.value)
                
                if precio_sin_iva <= 0 or stock < 0 or critico < 0:
                    show_message("⚠️ Los valores deben ser positivos", "orange")
                    return
                
                # Calcular precio con IVA (19%)
                precio_con_iva = precio_sin_iva * 1.19
                
                model.add_product(nombre, precio_con_iva, stock, critico)
                show_message(f"✅ '{nombre}' agregado - Precio final: ${precio_con_iva:,.0f} (IVA incluido)", "green")
                
                name_field.value = ""
                price_field.value = ""
                stock_field.value = ""
                critic_field.value = ""
                price_preview.value = "Precio con IVA (19%): $0"
                
                refresh_products()
            except sqlite3.IntegrityError:
                show_message(f"⚠️ '{nombre}' ya existe en el inventario", "orange")
            except ValueError:
                show_message("❌ Error: Verifica que precio y stock sean números válidos", "red")
            except Exception as ex:
                show_message(f"❌ Error: {str(ex)}", "red")
        
        def delete_product(product_id):
            model.delete_product(product_id)
            show_message("🗑️ Producto eliminado", "blue")
            refresh_products()
        
        def open_add_stock_dialog(product_id):
            qty_field = ft.TextField(
                label="Cantidad a agregar",
                keyboard_type=ft.KeyboardType.NUMBER,
                hint_text="10",
                autofocus=True,
            )
            
            def add_stock(e):
                try:
                    cantidad = int(qty_field.value)
                    if cantidad <= 0:
                        show_message("⚠️ La cantidad debe ser positiva", "orange")
                        return
                    
                    model.increase_stock_by_id(product_id, cantidad)
                    dlg.open = False
                    page.update()
                    show_message(f"✅ Stock aumentado en {cantidad} unidades", "green")
                    refresh_products()
                except ValueError:
                    show_message("❌ Ingresa un número válido", "red")
            
            dlg = ft.AlertDialog(
                title=ft.Text("➕ Sumar Stock"),
                content=qty_field,
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg)),
                    ft.TextButton("Agregar", on_click=add_stock),
                ],
            )
            page.overlay.append(dlg)
            dlg.open = True
            page.update()
        
        def open_edit_dialog(product_id, product_data):
            p_id, p_name, p_price, p_stock, p_crit = product_data
            
            edit_name = ft.TextField(label="Nombre", value=p_name)
            edit_price = ft.TextField(label="Precio", value=str(p_price), keyboard_type=ft.KeyboardType.NUMBER)
            edit_stock = ft.TextField(label="Stock", value=str(p_stock), keyboard_type=ft.KeyboardType.NUMBER)
            edit_critic = ft.TextField(label="Crítico", value=str(p_crit), keyboard_type=ft.KeyboardType.NUMBER)
            
            def save_edit(e):
                try:
                    nombre = edit_name.value.strip()
                    precio = float(edit_price.value)
                    stock = int(edit_stock.value)
                    critico = int(edit_critic.value)
                    
                    if not nombre or precio <= 0 or stock < 0 or critico < 0:
                        show_message("⚠️ Verifica los valores", "orange")
                        return
                    
                    model.update_product(product_id, nombre, precio, stock, critico)
                    dlg_edit.open = False
                    page.update()
                    show_message(f"✅ '{nombre}' actualizado correctamente", "green")
                    refresh_products()
                except ValueError:
                    show_message("❌ Error: Verifica los números", "red")
            
            dlg_edit = ft.AlertDialog(
                title=ft.Text("✏️ Editar Producto"),
                content=ft.Column([
                    edit_name,
                    edit_price,
                    edit_stock,
                    edit_critic,
                ], tight=True, height=250),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_edit)),
                    ft.TextButton("Guardar", on_click=save_edit),
                ],
            )
            page.overlay.append(dlg_edit)
            dlg_edit.open = True
            page.update()
        
        def close_dialog(dlg):
            dlg.open = False
            page.update()
        
        refresh_products()
        
        # Preparar layout de campos según tamaño de pantalla
        if is_mobile():
            # Móvil: todos los campos apilados verticalmente
            form_fields = ft.Column([
                name_field,
                price_field,
                stock_field,
                critic_field,
            ], spacing=10)
        else:
            # Desktop: nombre arriba, otros 3 en fila
            form_fields = ft.Column([
                name_field,
                ft.Row([
                    price_field,
                    stock_field,
                    critic_field,
                ], spacing=10),
            ], spacing=10)
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Text("📋 GESTIÓN DE INVENTARIO", size=24, weight="bold", color="white"),
                    bgcolor="#2196F3",
                    padding=20,
                    border_radius=ft.border_radius.only(top_left=10, top_right=10),
                ),
                # Instrucciones
                ft.Container(
                    content=ft.Text(
                        "➕ Completa el formulario para agregar nuevos productos:",
                        size=14,
                        color="black",
                        weight="bold"
                    ),
                    bgcolor="#e3f2fd",
                    padding=10,
                ),
                # Formulario y Buscador (lado a lado en desktop, apilados en móvil)
                # Formulario y Buscador con ResponsiveRow
                ft.ResponsiveRow([
                    # Formulario (12/12 en móvil, 8/12 en desktop)
                    ft.Container(
                        content=ft.Column([
                            form_fields,
                            ft.Column([
                                price_preview,
                                ft.ElevatedButton(
                                    "➕ AGREGAR PRODUCTO",
                                    on_click=add_product,
                                    bgcolor="#4CAF50",
                                    color="white",
                                    height=50,
                                    expand=True,
                                ),
                            ], spacing=10, horizontal_alignment="start", expand=True),
                        ], spacing=15),
                        bgcolor="#f5f5f5",
                        padding=20,
                        border_radius=10,
                        border=ft.border.all(2, "#2196F3"),
                        col={"xs": 12, "md": 8},
                    ),
                    # Buscador (12/12 en móvil, 4/12 en desktop)
                    ft.Container(
                        content=ft.Column([
                            ft.Text("🔍 BUSCAR PRODUCTOS", size=16, weight="bold", color="black", text_align="center"),
                            search_inventory,
                        ], spacing=10, horizontal_alignment="center"),
                        bgcolor="white",
                        padding=20,
                        border_radius=10,
                        border=ft.border.all(2, "#2196F3"),
                        col={"xs": 12, "md": 4},
                    ),
                ], spacing=10),
                # Título de la lista
                ft.Container(
                    content=ft.Text("📦 PRODUCTOS REGISTRADOS", size=18, weight="bold", color="black"),
                    bgcolor="#e3f2fd",
                    padding=10,
                    margin=ft.margin.only(left=10, right=10),
                ),
                # Lista
                ft.Container(
                    content=product_list,
                    expand=True,
                    margin=ft.margin.only(left=10, right=10, bottom=10),
                ),
            ], spacing=0, expand=True),
            bgcolor="white",
            border_radius=10,
            margin=10,
            expand=True,
        )
    
    # ========== NAVEGACIÓN CON PESTAÑAS SUPERIORES ==========
    current_tab = {"index": 0}  # 0 = Venta, 1 = Inventario
    main_content = ft.Ref[ft.Container]()
    
    def switch_tab(index):
        current_tab["index"] = index
        
        # Actualizar contenido
        if index == 0:
            main_content.current.content = build_pos_view()
        else:
            main_content.current.content = build_inventory_view()
        
        # Actualizar colores de botones
        btn_venta.bgcolor = "#2196F3" if index == 0 else "#90CAF9"
        btn_venta.color = "white" if index == 0 else "black"
        btn_inventario.bgcolor = "#2196F3" if index == 1 else "#90CAF9"
        btn_inventario.color = "white" if index == 1 else "black"
        
        page.update()
    
    # Botones de navegación
    btn_venta = ft.ElevatedButton(
        "🛒 PUNTO DE VENTA" if not is_mobile() else "🛒 Venta",
        on_click=lambda e: switch_tab(0),
        bgcolor="#2196F3",
        color="white",
        height=50,
        expand=True,
    )
    
    btn_inventario = ft.ElevatedButton(
        "📋 INVENTARIO" if not is_mobile() else "📋 Inventario",
        on_click=lambda e: switch_tab(1),
        bgcolor="#90CAF9",
        color="black",
        height=50,
        expand=True,
    )
    
    # Barra de navegación superior
    nav_bar = ft.Container(
        content=ft.Row([
            btn_venta,
            btn_inventario,
        ], spacing=10, alignment="center"),
        bgcolor="#f5f5f5",
        padding=10,
        border=ft.border.only(bottom=ft.BorderSide(2, "#2196F3")),
    )
    
    # Contenedor principal
    content_container = ft.Container(ref=main_content, expand=True)
    content_container.content = build_pos_view()
    
    # Layout principal
    page.add(
        ft.Column([
            nav_bar,
            content_container,
        ], spacing=0, expand=True)
    )
    page.update()

if __name__ == "__main__":
    import sys
    
    # Soporte para modo web (móvil/navegador)
    if "--web" in sys.argv:
        port = 8000
        if "--port" in sys.argv:
            port_index = sys.argv.index("--port")
            port = int(sys.argv[port_index + 1])
        
        print(f"🌐 Servidor web iniciado en puerto {port}")
        print(f"📱 Accede desde tu celular: http://TU_IP_LOCAL:{port}")
        ft.app(main, view=ft.AppView.WEB_BROWSER, port=port)
    else:
        # Modo desktop (ventana nativa)
        ft.app(main)
