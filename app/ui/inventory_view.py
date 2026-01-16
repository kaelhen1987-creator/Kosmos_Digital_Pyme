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
    barcode_field = ft.TextField(
        label="Código de Barras (Opcional)",
        bgcolor="white",
        color="black",
        border_color="#2196F3",
        hint_text="Ej: 7891234567890",
        expand=True,
        filled=True,
        border_width=2,
    )
    category_field = ft.Dropdown(
        label="Categoría",
        bgcolor="white",
        border_color="#2196F3",
        color="black",
        label_style=ft.TextStyle(color="black"),
        filled=True,
        border_width=2,
        expand=True,
        options=[
            ft.dropdown.Option("General"),
            ft.dropdown.Option("Bebidas"),
            ft.dropdown.Option("Cafés"),
            ft.dropdown.Option("Sandwiches"),
            ft.dropdown.Option("Pastelería"),
            ft.dropdown.Option("Almacén"),
            ft.dropdown.Option("Cigarros"),
            ft.dropdown.Option("Lácteos"),
            ft.dropdown.Option("Aseo"),
        ],
        hint_text="Categoría", # Mostrar esto cuando no hay selección
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
        expand=True,
    )
    
    def refresh_products(search_query=""):
        product_list.controls.clear()
        products = model.get_all_products()
        
        # Filtrar por búsqueda
        if search_query:
            products = [p for p in products if search_query.lower() in p[1].lower()]
        
        if not products:
             # ... (empty state) ...
             pass
        else:
            for p in products:
                # Desempaquetar producto (ahora incluye categoria)
                # Schema: id, nombre, precio, stock, critico, barcode, categoria
                p_cat = "General"
                if len(p) >= 7:
                    p_id, p_name, p_price, p_stock, p_crit, p_barcode, p_cat = p
                elif len(p) == 6:
                    p_id, p_name, p_price, p_stock, p_crit, p_barcode = p
                else:
                    p_id, p_name, p_price, p_stock, p_crit = p
                    p_barcode = None
                
                # Check None
                if not p_cat: p_cat = "General"
                
                bg_color = "white"
                if p_stock <= p_crit:
                    bg_color = "#ffcccc"
                elif p_stock <= p_crit + 5:
                    bg_color = "#fff9c4"
                
                product_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            # Fila 1: Nombre y Categoria + Menú
                            ft.Row([
                                ft.Column([
                                    ft.Text(f"{p_name}", size=18, weight="bold", color="black"),
                                    ft.Container(
                                        content=ft.Text(p_cat.upper(), size=10, color="white"),
                                        bgcolor="green", padding=3, border_radius=4
                                    )
                                ], spacing=2),
                                ft.PopupMenuButton(
                                    icon=ft.Icons.MORE_VERT,
                                    icon_color="black",
                                    items=[
                                        ft.PopupMenuItem(
                                            content=ft.Text("Editar"), 
                                            icon=ft.Icons.EDIT, 
                                            on_click=lambda e, pid=p_id, pdata=p: open_edit_dialog(pid, pdata)
                                        ),
                                        ft.PopupMenuItem(
                                            content=ft.Text("Eliminar", color="red"),
                                            icon=ft.Icons.DELETE, 
                                            on_click=lambda e, pid=p_id: delete_product(pid)
                                        ),
                                        ft.PopupMenuItem(
                                            content=ft.Text("Agregar Stock"), 
                                            icon=ft.Icons.ADD_BOX, 
                                            on_click=lambda e, pid=p_id: quick_add_stock(pid)
                                        ),
                                    ]
                                ),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            
                            ft.Divider(color="grey"),
                            
                            # Fila 2: Detalles (Precio, Stock, Critico)
                            ft.Row([
                                ft.Column([
                                    ft.Text("Precio", size=12, color="grey"),
                                    ft.Text(f"${p_price:,.0f}", size=16, weight="bold", color="black")
                                ]),
                                ft.Column([
                                    ft.Text("Stock", size=12, color="grey"),
                                    ft.Text(f"{p_stock}", size=16, weight="bold", color="red" if p_stock <= p_crit else "black")
                                ]),
                                ft.Column([
                                    ft.Text("Crítico", size=12, color="grey"),
                                    ft.Text(f"{p_crit}", size=16, color="black")
                                ]),
                                ft.Column([
                                    ft.Text("Código", size=12, color="grey"),
                                    ft.Text(f"{p_barcode if p_barcode else '--'}", size=14, color="black")
                                ]),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
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
            
            codigo_barras = barcode_field.value.strip() if barcode_field.value else None
            categoria = category_field.value
            if not categoria: categoria = "General"
            
            precio_sin_iva = float(price_field.value)
            stock = int(stock_field.value)
            critico = int(critic_field.value)
            
            if precio_sin_iva <= 0 or stock < 0 or critico < 0:
                show_message(page, "Los valores deben ser positivos", "orange")
                return
            
            # Calcular precio con IVA (19%)
            precio_con_iva = precio_sin_iva * 1.19
            
            model.add_product(nombre, precio_con_iva, stock, critico, codigo_barras, categoria)
            show_message(page, f"'{nombre}' agregado - Precio final: ${precio_con_iva:,.0f} (IVA incluido)", "green")
            
            name_field.value = ""
            barcode_field.value = ""
            category_field.value = "General"
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
    
    # ...

    def delete_product(product_id):
        try:
            model.delete_product(product_id)
            show_message(page, "Producto eliminado", "green")
            refresh_products()
        except Exception as ex:
            show_message(page, f"Error al eliminar: {str(ex)}", "red")

    def quick_add_stock(product_id):
        add_stock_field = ft.TextField(label="Cantidad a agregar", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
        
        def confirm_add(e):
            try:
                qty = int(add_stock_field.value)
                if qty <= 0:
                    show_message(page, "La cantidad debe ser mayor a 0", "orange")
                    return
                
                model.update_stock(product_id, qty)
                dlg_stock.open = False
                page.update()
                show_message(page, f"Stock agregado correctamente", "green")
                refresh_products()
            except ValueError:
                show_message(page, "Cantidad inválida", "red")
            except Exception as ex:
                show_message(page, f"Error: {str(ex)}", "red")

        dlg_stock = ft.AlertDialog(
            title=ft.Text("Agregar Stock Rápido"),
            content=add_stock_field,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_stock)),
                ft.TextButton("Agregar", on_click=confirm_add),
            ],
        )
        page.overlay.append(dlg_stock)
        dlg_stock.open = True
        page.update()
    
    def open_edit_dialog(product_id, product_data):
        # Desempaquetar
        p_cat = "General"
        if len(product_data) >= 7:
            p_id, p_name, p_price, p_stock, p_crit, p_barcode, p_cat = product_data
        elif len(product_data) == 6:
            p_id, p_name, p_price, p_stock, p_crit, p_barcode = product_data
        else:
            p_id, p_name, p_price, p_stock, p_crit = product_data
            p_barcode = None
        
        edit_name = ft.TextField(label="Nombre", value=p_name)
        edit_barcode = ft.TextField(label="Código de Barras", value=p_barcode if p_barcode else "")
        edit_cat = ft.Dropdown(
            label="Categoría",
            options=[
                ft.dropdown.Option("General"),
                ft.dropdown.Option("Bebidas"),
                ft.dropdown.Option("Cafés"),
                ft.dropdown.Option("Sandwiches"),
                ft.dropdown.Option("Pastelería"),
                ft.dropdown.Option("Almacén"),
                ft.dropdown.Option("Cigarros"),
                ft.dropdown.Option("Lácteos"),
                ft.dropdown.Option("Aseo"),
            ],
            value=p_cat if p_cat else "General"
        )
        edit_price = ft.TextField(label="Precio", value=str(p_price), keyboard_type=ft.KeyboardType.NUMBER)
        edit_stock = ft.TextField(label="Stock", value=str(p_stock), keyboard_type=ft.KeyboardType.NUMBER)
        edit_critic = ft.TextField(label="Crítico", value=str(p_crit), keyboard_type=ft.KeyboardType.NUMBER)
        
        def save_edit(e):
            try:
                nombre = edit_name.value.strip()
                codigo_barras = edit_barcode.value.strip() if edit_barcode.value else None
                cat = edit_cat.value
                
                precio = float(edit_price.value)
                stock = int(edit_stock.value)
                critico = int(edit_critic.value)
                
                if not nombre or precio <= 0 or stock < 0 or critico < 0:
                    show_message(page, "Verifica los valores", "orange")
                    return
                
                model.update_product(product_id, nombre, precio, stock, critico, codigo_barras, cat)
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
                edit_barcode,
                edit_cat,
                edit_price,
                edit_stock,
                edit_critic,
            ], tight=True, height=350),
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
    
    # Layout unificado (Responsive Grid)
    form_fields = ft.ResponsiveRow([
        ft.Container(name_field, col={"xs": 12, "md": 12}),
        ft.Container(barcode_field, col={"xs": 12, "md": 6}),
        ft.Container(category_field, col={"xs": 12, "md": 6}),
        ft.Container(price_field, col={"xs": 12, "md": 4}),
        ft.Container(stock_field, col={"xs": 12, "md": 4}),
        ft.Container(critic_field, col={"xs": 12, "md": 4}),
    ], spacing=10)

    return ft.Container(
        content=ft.Column([
            # Header
            ft.Container(
                content=ft.Text("INVENTARIO", size=22, weight="bold", color="white"),
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
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO),
        bgcolor="white",
        border_radius=10,
        margin=10,
        expand=True,
    )
