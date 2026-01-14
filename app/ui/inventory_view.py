import flet as ft
import sqlite3
from app.utils.helpers import is_mobile, show_message

def build_inventory_view(page: ft.Page, model):
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
                price_preview.value = f"Precio con IVA (19%): ${precio_con_iva:,.0f}"
            else:
                price_preview.value = "Precio con IVA (19%): $0"
            price_preview.update()
        except ValueError:
            price_preview.value = "Precio con IVA (19%): $0"
            price_preview.update()
    
    product_list = ft.ListView(spacing=10, padding=10, expand=True)
    
    # Campo de búsqueda para inventario
    search_inventory = ft.TextField(
        hint_text="Buscar en inventario...",
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
                        "No hay productos registrados\n\nUsa el formulario arriba para agregar productos",
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
                if p_stock <= p_crit:
                    bg_color = "#ffcccc"
                elif p_stock <= p_crit + 5:
                    bg_color = "#fff9c4"
                
                product_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            # Fila 1: Nombre del producto
                            ft.Row([
                                ft.Text(
                                    f"{p_name}", 
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
                                        ft.Text("Precio:", size=14, weight="bold"),
                                        ft.Text(f"${p_price:,.0f}", size=14, color="black"),
                                    ], spacing=5),
                                    ft.Row([
                                        ft.Text("Stock:", size=14, weight="bold"),
                                        ft.Text(f"{p_stock}", size=14, color="black"),
                                    ], spacing=5),
                                    ft.Row([
                                        ft.Text("Critico:", size=14, weight="bold"),
                                        ft.Text(f"{p_crit}", size=14, color="black"),
                                    ], spacing=5),
                                ], spacing=3, expand=True),
                                # Columna derecha: Botones de acción (todos verticales)
                                ft.Column([
                                    ft.TextButton(
                                        "Sumar Stock",
                                        on_click=lambda e, pid=p_id: open_add_stock_dialog(pid),
                                        style=ft.ButtonStyle(color="blue"),
                                    ),
                                    ft.TextButton(
                                        "Editar",
                                        on_click=lambda e, pid=p_id, pdata=p: open_edit_dialog(pid, pdata),
                                        style=ft.ButtonStyle(color="orange"),
                                    ),
                                    ft.TextButton(
                                        "Eliminar",
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
                show_message(page, "Ingresa el nombre del producto", "orange")
                return
            
            precio_sin_iva = float(price_field.value)
            stock = int(stock_field.value)
            critico = int(critic_field.value)
            
            if precio_sin_iva <= 0 or stock < 0 or critico < 0:
                show_message(page, "Los valores deben ser positivos", "orange")
                return
            
            # Calcular precio con IVA (19%)
            precio_con_iva = precio_sin_iva * 1.19
            
            model.add_product(nombre, precio_con_iva, stock, critico)
            show_message(page, f"'{nombre}' agregado - Precio final: ${precio_con_iva:,.0f} (IVA incluido)", "green")
            
            name_field.value = ""
            price_field.value = ""
            stock_field.value = ""
            critic_field.value = ""
            price_preview.value = "Precio con IVA (19%): $0"
            
            refresh_products()
        except sqlite3.IntegrityError:
            show_message(page, f"'{nombre}' ya existe en el inventario", "orange")
        except ValueError:
            show_message(page, "Error: Verifica que precio y stock sean números válidos", "red")
        except Exception as ex:
            show_message(page, f"Error: {str(ex)}", "red")
    
    def delete_product(product_id):
        model.delete_product(product_id)
        show_message(page, "Producto eliminado", "blue")
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
                    show_message(page, "La cantidad debe ser positiva", "orange")
                    return
                
                model.increase_stock_by_id(product_id, cantidad)
                dlg.open = False
                page.update()
                show_message(page, f"Stock aumentado en {cantidad} unidades", "green")
                refresh_products()
            except ValueError:
                show_message(page, "Ingresa un número válido", "red")
        
        dlg = ft.AlertDialog(
            title=ft.Text("Sumar Stock"),
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
                    show_message(page, "Verifica los valores", "orange")
                    return
                
                model.update_product(product_id, nombre, precio, stock, critico)
                dlg_edit.open = False
                page.update()
                show_message(page, f"'{nombre}' actualizado correctamente", "green")
                refresh_products()
            except ValueError:
                show_message(page, "Error: Verifica los números", "red")
        
        dlg_edit = ft.AlertDialog(
            title=ft.Text("Editar Producto"),
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
    if is_mobile(page):
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
                content=ft.Text("GESTIÓN DE INVENTARIO", size=24, weight="bold", color="white"),
                bgcolor="#2196F3",
                padding=20,
                border_radius=ft.border_radius.only(top_left=10, top_right=10),
            ),
            # Instrucciones
            ft.Container(
                content=ft.Text(
                    "Completa el formulario para agregar nuevos productos:",
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
                                "AGREGAR PRODUCTO",
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
                        ft.Text("BUSCAR PRODUCTOS", size=16, weight="bold", color="black", text_align="center"),
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
                content=ft.Text("PRODUCTOS REGISTRADOS", size=18, weight="bold", color="black"),
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
