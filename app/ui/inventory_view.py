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
    category_dropdown = ft.Dropdown(
        label="Categoría",
        bgcolor="white",
        border_color="#2196F3",
        color="black",
        label_style=ft.TextStyle(color="black"),
        filled=True,
        border_width=2,
        expand=True,
        options=[ft.dropdown.Option(c) for c in model.get_all_categories()],
        value="General",
        hint_text="Categoría",
    )

    def open_add_category_dialog(e):
        new_cat_field = ft.TextField(
            label="Nombre de la Categoría", 
            autofocus=True,
            max_length=20,
            hint_text="Ej: Mascotas"
        )
        
        def save_category(e):
            name = new_cat_field.value.strip().title()
            if not name:
                new_cat_field.error_text = "El nombre no puede estar vacío"
                new_cat_field.update()
                return
            
            if name == "Todas":
                new_cat_field.error_text = "'Todas' es un nombre reservado"
                new_cat_field.update()
                return
            
            if name:
                model.add_category(name)
                # Actualizar opciones del dropdown
                new_cats = model.get_all_categories()
                category_dropdown.options = [ft.dropdown.Option(c) for c in new_cats]
                category_dropdown.value = name
                category_dropdown.update()
                show_message(page, f"Categoría '{name}' agregada", "green")
                dlg_cat.open = False
                page.update()
            else:
                new_cat_field.error_text = "Ingrese un nombre"
                new_cat_field.update()

        dlg_cat = ft.AlertDialog(
            title=ft.Text("Nueva Categoría"),
            content=new_cat_field,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_cat)),
                ft.FilledButton("Guardar", on_click=save_category),
            ],
        )
        page.overlay.append(dlg_cat)
        dlg_cat.open = True
        page.update()

    def open_manage_categories_dialog(e):
        lista_categorias_ui = ft.Column(scroll=ft.ScrollMode.AUTO, height=300, spacing=10)

        def actualizar_dropdown_principal():
            opciones = model.get_all_categories()
            category_dropdown.options = [ft.dropdown.Option(cat) for cat in opciones]
            if category_dropdown.value not in opciones:
                category_dropdown.value = "General"
            category_dropdown.update()

        def recargar_lista():
            lista_categorias_ui.controls.clear()
            for cat in model.get_all_categories():
                es_protegida = cat in ["General", "Todas"]
                
                lista_categorias_ui.controls.append(
                    ft.Container(
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(cat, weight="bold", color="black"),
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        icon_color="blue",
                                        tooltip="Editar",
                                        on_click=lambda e, c=cat: abrir_dialogo_edicion_cat(c)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_color="red",
                                        tooltip="Eliminar",
                                        disabled=es_protegida,
                                        on_click=lambda e, c=cat: confirmar_borrado_cat(c)
                                    )
                                ], spacing=0)
                            ]
                        ),
                        bgcolor="#f5f5f5",
                        padding=10,
                        border_radius=5
                    )
                )
            page.update()

        def abrir_dialogo_edicion_cat(nombre_viejo):
            txt_nuevo_nombre = ft.TextField(label="Nuevo nombre", value=nombre_viejo, autofocus=True, max_length=20)
            
            def guardar_edicion(e):
                nuevo_nombre = txt_nuevo_nombre.value.strip().title()
                if not nuevo_nombre:
                    txt_nuevo_nombre.error_text = "El nombre no puede estar vacío"
                    txt_nuevo_nombre.update()
                    return
                if nuevo_nombre == "Todas":
                    txt_nuevo_nombre.error_text = "'Todas' es reservado"
                    txt_nuevo_nombre.update()
                    return
                    
                if model.update_category(nombre_viejo, nuevo_nombre):
                    recargar_lista()
                    actualizar_dropdown_principal()
                    dialogo_editar.open = False
                    show_message(page, f"Categoría '{nombre_viejo}' actualizada a '{nuevo_nombre}'", "green")
                    page.update()

            dialogo_editar = ft.AlertDialog(
                title=ft.Text(f"Editar: {nombre_viejo}"),
                content=txt_nuevo_nombre,
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dialogo_editar)),
                    ft.FilledButton("Guardar", on_click=guardar_edicion)
                ]
            )
            page.overlay.append(dialogo_editar)
            dialogo_editar.open = True
            page.update()

        def confirmar_borrado_cat(nombre_cat):
            def proceder_borrado(e):
                if model.delete_category(nombre_cat):
                    recargar_lista()
                    actualizar_dropdown_principal()
                    dialogo_borrar.open = False
                    show_message(page, f"Categoría '{nombre_cat}' eliminada. Productos movidos a 'General'.", "orange")
                    page.update()

            dialogo_borrar = ft.AlertDialog(
                title=ft.Text("Confirmar Eliminación"),
                content=ft.Text(f"¿Estás seguro de eliminar '{nombre_cat}'?\nLos productos asociados pasarán a 'General'."),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dialogo_borrar)),
                    ft.FilledButton("Eliminar", icon=ft.Icons.DELETE, bgcolor="red", color="white", on_click=proceder_borrado)
                ]
            )
            page.overlay.append(dialogo_borrar)
            dialogo_borrar.open = True
            page.update()

        recargar_lista()

        dlg_manage = ft.AlertDialog(
            title=ft.Text("Gestionar Categorías"),
            content=ft.Container(content=lista_categorias_ui, width=400),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: close_dialog(dlg_manage))
            ]
        )
        page.overlay.append(dlg_manage)
        dlg_manage.open = True
        page.update()

    category_field = ft.Row([
        category_dropdown,
        ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE,
            icon_color="#2196F3",
            tooltip="Nueva Categoría",
            on_click=open_add_category_dialog
        ),
        ft.IconButton(
            icon=ft.Icons.SETTINGS,
            icon_color="#2196F3",
            tooltip="Gestionar Categorías",
            on_click=open_manage_categories_dialog
        )
    ], alignment=ft.MainAxisAlignment.START, spacing=0)
    
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
        label="Stock Inicial (Opcional)",
        bgcolor="white",
        color="black",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color="#2196F3",
        hint_text="0",
        filled=True,
        border_width=2,
        expand=1,
    )
    critic_field = ft.TextField(
        label="Stock Crítico (Opcional)",
        bgcolor="white",
        color="black",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color="#2196F3",
        hint_text="0",
        filled=True,
        border_width=2,
        expand=1,
    )
    expiration_field = ft.TextField(
        label="Vencimiento (Opcional)",
        bgcolor="white",
        color="black",
        border_color="#2196F3",
        hint_text="YYYY-MM-DD",
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
    
    product_grid = ft.Row(
        wrap=True,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=10,
        run_spacing=10,
    )
    
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
        product_grid.controls.clear()
        products = model.get_all_products()
        
        if search_query:
            products = [p for p in products if search_query.lower() in p[1].lower()]
        
        if not products:
             pass
        else:
            for p in products:
                # Schema: id, nombre, precio, stock, critico, barcode, categoria, vencimiento
                p_id, p_name, p_price, p_stock, p_crit, p_barcode, p_cat, p_exp = None, None, 0, 0, 0, None, "General", None
                
                if len(p) >= 8:
                    p_id, p_name, p_price, p_stock, p_crit, p_barcode, p_cat, p_exp = p[:8]
                elif len(p) == 7:
                    p_id, p_name, p_price, p_stock, p_crit, p_barcode, p_cat = p[:7]
                elif len(p) == 6:
                    p_id, p_name, p_price, p_stock, p_crit, p_barcode = p[:6]
                else:
                    p_id, p_name, p_price, p_stock, p_crit = p[:5]
                
                if not p_cat: p_cat = "General"
                
                is_critic = p_stock <= p_crit
                border_color = "red" if is_critic else "transparent"
                stock_color = "red" if is_critic else "green"
                stock_icon = ft.Icons.WARNING_ROUNDED if is_critic else ft.Icons.CHECK
                
                subtitle = f"{p_cat}"
                if p_exp: subtitle += f" · Vence {p_exp}"

                product_grid.controls.append(
                    ft.Container(
                        width=280,
                        content=ft.Column([
                            ft.Row([
                                ft.Column([
                                    ft.Text(p_name, size=16, weight="bold", color="white", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(subtitle, size=12, color="#888888", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
                                ], spacing=0, expand=True),
                                ft.PopupMenuButton(
                                    icon=ft.Icons.MORE_VERT,
                                    icon_color="#888888",
                                    items=[
                                        ft.PopupMenuItem(content=ft.Text("Editar"), icon=ft.Icons.EDIT, on_click=lambda e, pid=p_id, pdata=p: open_edit_dialog(pid, pdata)),
                                        ft.PopupMenuItem(content=ft.Text("Agregar Stock"), icon=ft.Icons.ADD_BOX, on_click=lambda e, pid=p_id: quick_add_stock(pid)),
                                        ft.PopupMenuItem(content=ft.Text("Eliminar", color="red"), icon=ft.Icons.DELETE, on_click=lambda e, pid=p_id, pname=p_name: delete_product(pid, pname)),
                                    ]
                                ),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            
                            ft.Row([
                                ft.Text(f"${p_price:,.0f}", size=18, weight="bold", color="white"),
                                ft.Row([
                                    ft.Text(f"Stock: {p_stock}", size=14, weight="bold", color=stock_color),
                                    ft.Icon(stock_icon, size=14, color=stock_color)
                                ], spacing=2)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ], spacing=10),
                        bgcolor="#2c2c2c",
                        padding=15,
                        border_radius=8,
                        border=ft.border.only(left=ft.border.BorderSide(4, border_color), top=ft.border.BorderSide(1, "#3a3a3a"), right=ft.border.BorderSide(1, "#3a3a3a"), bottom=ft.border.BorderSide(1, "#3a3a3a"))
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
            categoria = category_dropdown.value
            if not categoria: categoria = "General"
            
            expiration = expiration_field.value.strip() if expiration_field.value else None
            
            precio_sin_iva = float(price_field.value)
            
            # Stock y Crítico son opcionales (Default 0)
            stock_val = stock_field.value.strip() if stock_field.value else ""
            stock = int(stock_val) if stock_val else 0
            
            crit_val = critic_field.value.strip() if critic_field.value else ""
            critico = int(crit_val) if crit_val else 0
            
            if precio_sin_iva <= 0 or stock < 0 or critico < 0:
                show_message(page, "Los valores deben ser positivos", "orange")
                return
            
            # Calcular precio con IVA (19%)
            precio_con_iva = precio_sin_iva * 1.19
            
            model.add_product(nombre, precio_con_iva, stock, critico, codigo_barras, categoria, fecha_vencimiento=expiration)
            show_message(page, f"'{nombre}' agregado - Precio final: ${precio_con_iva:,.0f} (IVA incluido)", "green")
            
            name_field.value = ""
            barcode_field.value = ""
            category_dropdown.value = "General"
            price_field.value = ""
            stock_field.value = ""
            critic_field.value = ""
            expiration_field.value = ""
            price_preview.value = "Precio con IVA (19%): $0"
            
            refresh_products()
        except sqlite3.IntegrityError:
            show_message(page, f"'{nombre}' ya existe en el inventario", "orange")
        except ValueError:
            show_message(page, "Error: Verifica que precio y stock sean números válidos", "red")
        except Exception as ex:
            show_message(page, f"Error: {str(ex)}", "red")
    
    # ... (delete_product, quick_add_stock, open_promo_dialog skipped as they don't change logic significantly) ...
    # Wait, open_edit_dialog DOES need changes.
    # Inserting full block including Quick Add/Promo/Edit to ensure context match or skipping safely?
    # I will replace up to 'def delete_product' and then handle 'open_edit_dialog' separately to avoid huge chunk.
    # Actually, the user asked for fewer tools. I should try to do logic in one go, but the chunk limitation is real.
    # I'll replace the block from `critic_field` definition down to `add_product` end.
    
    # ... (Existing implementations of delete/quick/promo remain same in file but need to update open_edit_dialog next) ...
    
    # To handle 'open_edit_dialog' correctly without replacing 300 lines, I will issue a second replace call.
    # This block covers `add_product` fully.
    
    pass 

    # For the replacement below, I'm replacing from 'critic_field =' down to end of 'add_product'.
    
    # --- END OF REPLACEMENT STRING ---

# NOTE: Since I can't put Python logic in thought, I will execute the tool.
# The `add_product` function ends around line 258. `delete_product` is at 261.
# I am replacing from line 73 to 258.

    pass
    
    # ...

    def delete_product(product_id, product_name="este producto"):
        def confirm_delete(e):
            dlg_confirm.open = False
            page.update()
            try:
                model.delete_product(product_id)
                show_message(page, f"'{product_name}' eliminado.", "green")
                refresh_products()
            except Exception as ex:
                show_message(page, f"Error al eliminar: {str(ex)}", "red")

        def cancel_delete(e):
            dlg_confirm.open = False
            page.update()

        dlg_confirm = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING_ROUNDED, color="#F44336", size=22),
                ft.Text("¿Eliminar producto?", color="white", size=16, weight="bold")
            ], spacing=8),
            content=ft.Text(
                f"Estás por eliminar \"{product_name}\".\n\nEsta acción no se puede deshacer.",
                color="#aaaaaa", size=13
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancel_delete,
                              style=ft.ButtonStyle(color="#aaaaaa")),
                ft.FilledButton(
                    "Sí, eliminar",
                    icon=ft.Icons.DELETE_FOREVER,
                    style=ft.ButtonStyle(bgcolor="#D32F2F", color="white",
                                        shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=confirm_delete
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#1e1e1e",
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        page.overlay.append(dlg_confirm)
        dlg_confirm.open = True
        page.update()


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
    
    def open_promo_dialog(e):
        # Estados Locales del Dialogo
        promo_components = {} # {pid: {'name': name, 'qty': qty}}
        
        # UI Elements
        p_name = ft.TextField(label="Nombre Promoción", autofocus=True)
        p_price = ft.TextField(label="Precio", keyboard_type=ft.KeyboardType.NUMBER)
        p_search = ft.TextField(label="Buscar producto componente...", suffix_icon=ft.Icons.SEARCH)
        
        comp_list = ft.Column(scroll=ft.ScrollMode.AUTO, height=200)
        search_results = ft.Column(visible=False) # Resultados busqueda dropdown
        
        def refresh_components():
            comp_list.controls.clear()
            if not promo_components:
                comp_list.controls.append(ft.Text("Agrega productos al paquete", color="grey"))
            else:
                for pid, data in promo_components.items():
                    qty = data['qty']
                    comp_list.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(f"{data['name']}", size=14, expand=True),
                                ft.Row([
                                    ft.IconButton(ft.Icons.REMOVE_CIRCLE, icon_color="red", on_click=lambda e, i=pid: update_qty(i, -1)),
                                    ft.Text(f"{qty}", weight="bold"),
                                    ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color="green", on_click=lambda e, i=pid: update_qty(i, 1)),
                                ], spacing=0)
                            ]),
                            bgcolor="#f0f0f0", padding=5, border_radius=5
                        )
                    )
            dlg_promo.update()
        
        def update_qty(pid, delta):
            if pid in promo_components:
                promo_components[pid]['qty'] += delta
                if promo_components[pid]['qty'] <= 0:
                    del promo_components[pid]
            refresh_components()

        def add_component(product):
            # product: tuple from DB
            pid, name = product[0], product[1]
            if pid not in promo_components:
                promo_components[pid] = {'name': name, 'qty': 0}
            promo_components[pid]['qty'] += 1
            
            p_search.value = ""
            search_results.visible = False
            refresh_components()
            
        def search_comp(e):
            query = p_search.value.lower()
            search_results.controls.clear()
            if not query:
                search_results.visible = False
                dlg_promo.update()
                return

            all_prods = model.get_all_products()
            # Filtrar solo productos normales (no Promociones para evitar recursividad infinita simple)
            matches = [p for p in all_prods if query in p[1].lower() and p[6] != "Promociones"][:5]
            
            if matches:
                search_results.visible = True
                for p in matches:
                    search_results.controls.append(
                        ft.ListTile(
                            title=ft.Text(p[1]),
                            subtitle=ft.Text(f"Stock: {p[3]}"),
                            on_click=lambda e, prod=p: add_component(prod)
                        )
                    )
            else:
                search_results.visible = False
            dlg_promo.update()

        p_search.on_change = search_comp

        def save_promo(e):
            try:
                name = p_name.value
                price = float(p_price.value)
                if not name or price <= 0 or not promo_components:
                    show_message(page, "Completa nombre, precio y agrega componentes", "orange")
                    return
                
                # Preparar lista [(pid, qty)]
                comps_list = [(pid, data['qty']) for pid, data in promo_components.items()]
                
                model.add_promotion(name, price, comps_list)
                show_message(page, "Promoción creada exitosamente", "green")
                dlg_promo.open = False
                page.update()
                refresh_products()
                
            except Exception as ex:
                show_message(page, f"Error: {str(ex)}", "red")

        dlg_promo = ft.AlertDialog(
            title=ft.Text("Nueva Promoción (Pack)"),
            content=ft.Container(
                content=ft.Column([
                    p_name,
                    p_price,
                    ft.Divider(),
                    ft.Text("Componentes:", weight="bold"),
                    p_search,
                    ft.Container(content=search_results, bgcolor="white", border=ft.border.all(1, "grey"), border_radius=5),
                    comp_list
                ], spacing=10, scroll=ft.ScrollMode.AUTO),
                width=400, height=500
            ),
            actions=[
                 ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_promo)),
                 ft.FilledButton("Guardar Pack", on_click=save_promo, style=ft.ButtonStyle(bgcolor="green", color="white"))
            ]
        )
        page.overlay.append(dlg_promo)
        dlg_promo.open = True
        page.update()
        refresh_components()
    
    def open_edit_dialog(product_id, product_data):
        # Desempaquetar robusto
        p_cat = "General"
        p_exp = None
        
        if len(product_data) >= 8:
            p_id, p_name, p_price, p_stock, p_crit, p_barcode, p_cat, p_exp = product_data[:8]
        elif len(product_data) >= 7:
            p_id, p_name, p_price, p_stock, p_crit, p_barcode, p_cat = product_data[:7]
        elif len(product_data) == 6:
            p_id, p_name, p_price, p_stock, p_crit, p_barcode = product_data
        else:
            p_id, p_name, p_price, p_stock, p_crit = product_data
            p_barcode = None
        
        edit_name = ft.TextField(label="Nombre", value=p_name)
        edit_barcode = ft.TextField(label="Código de Barras", value=p_barcode if p_barcode else "")
        
        # Opciones dinámicas para el diálogo de edición
        current_cats = model.get_all_categories()
        edit_cat = ft.Dropdown(
            label="Categoría",
            options=[ft.dropdown.Option(c) for c in current_cats],
            value=p_cat if p_cat in current_cats else "General"
        )
        edit_price = ft.TextField(label="Precio", value=str(p_price), keyboard_type=ft.KeyboardType.NUMBER)
        edit_stock = ft.TextField(label="Stock (Opcional)", value=str(p_stock), keyboard_type=ft.KeyboardType.NUMBER)
        edit_critic = ft.TextField(label="Crítico (Opcional)", value=str(p_crit), keyboard_type=ft.KeyboardType.NUMBER)
        edit_exp = ft.TextField(label="Vencimiento (YYYY-MM-DD)", value=p_exp if p_exp else "")
        
        def save_edit(e):
            try:
                nombre = edit_name.value.strip()
                codigo_barras = edit_barcode.value.strip() if edit_barcode.value else None
                cat = edit_cat.value
                exp = edit_exp.value.strip() if edit_exp.value else None
                
                precio = float(edit_price.value)
                
                # Opcionales en Edición
                s_val = edit_stock.value.strip() if edit_stock.value else ""
                stock = int(s_val) if s_val else 0
                
                c_val = edit_critic.value.strip() if edit_critic.value else ""
                critico = int(c_val) if c_val else 0
                
                if not nombre or precio <= 0 or stock < 0 or critico < 0:
                    show_message(page, "Verifica los valores", "orange")
                    return
                
                model.update_product(product_id, nombre, precio, stock, critico, codigo_barras, cat, fecha_vencimiento=exp)
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
                edit_exp,
                ft.Container(height=10) # Spacer at bottom
            ], tight=True, scroll=ft.ScrollMode.AUTO, width=300),
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
    
    drawer_visible = True
    def toggle_drawer(e):
        nonlocal drawer_visible
        drawer_visible = not drawer_visible
        form_panel.visible = drawer_visible
        btn_toggle.text = "Ocultar" if drawer_visible else "Agregar"
        btn_toggle.icon = ft.Icons.ARROW_FORWARD if drawer_visible else ft.Icons.ADD
        btn_toggle.update()
        page.update()

    btn_toggle = ft.FilledButton(
        "Ocultar" if drawer_visible else "Agregar", 
        icon=ft.Icons.ARROW_FORWARD if drawer_visible else ft.Icons.ADD,
        on_click=toggle_drawer,
        style=ft.ButtonStyle(bgcolor="#4CAF50", color="white")
    )

    form_panel = ft.Container(
        width=320,
        padding=20,
        bgcolor="#1e1e1e",
        border_radius=ft.border_radius.only(top_right=10, bottom_right=10),
        border=ft.border.all(1, "#333333"),
        visible=drawer_visible,
        content=ft.Column([
            ft.Text("Nuevo Producto", size=20, weight="bold", color="white"),
            ft.Divider(height=10, color="transparent"),
            name_field,
            barcode_field,
            category_field,
            price_field,
            ft.Row([ft.Container(stock_field, expand=True), ft.Container(critic_field, expand=True)], spacing=10),
            expiration_field,
            price_preview,
            ft.Divider(height=10, color="transparent"),
            ft.FilledButton("Agregar", on_click=add_product, style=ft.ButtonStyle(bgcolor="#4CAF50", color="white"), height=45, expand=True, width=float("inf")),
            ft.Divider(),
            ft.TextButton("Nueva Promoción", icon=ft.Icons.NEW_LABEL, on_click=open_promo_dialog, expand=True, width=float("inf")),
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    )

    search_inventory.expand = True

    main_panel = ft.Container(
        expand=True,
        padding=20,
        bgcolor="#121212",
        content=ft.Column([
            ft.Row([
                ft.Text("Productos registrados", size=24, weight="bold", color="white"),
                btn_toggle
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Divider(height=10, color="transparent"),
            ft.Container(search_inventory, width=450),
            ft.Divider(height=15, color="transparent"),
            product_grid
        ], expand=True, spacing=0)
    )

    # Layout de la vista
    return ft.Container(
        content=ft.Row([
            main_panel,
            form_panel
        ], expand=True, spacing=0),
        bgcolor="#121212",
        border_radius=10,
        margin=10,
        expand=True
    )
