import flet as ft
from app.utils.helpers import is_mobile, show_message

def build_pos_view(page: ft.Page, model, shared_cart=None):
    # --- 1. STATE VARIABLES ---
    cart = shared_cart if shared_cart is not None else {}
    current_mode = "scanner" # "scanner" or "visual"
    current_category = "Todas"
    current_discount = [0] # Mutable state for discount percent
    last_expiring_count = [0]
    
    # --- 2. FORWARD REFS / UI CONTROLS (Placeholder initialized later) ---
    product_list = ft.Column(spacing=10, expand=False)
    grid_view = ft.GridView(expand=False, runs_count=5, max_extent=200, child_aspect_ratio=0.8, spacing=10, run_spacing=10)
    cart_list = ft.Column(spacing=5, expand=False)
    total_text = ft.Text("Total: $0", size=24, weight="bold", color="white")
    
    list_container = ft.Container(content=product_list)
    grid_container = ft.Container(content=grid_view, visible=False)

    # --- 3. LOGIC FUNCTIONS ---
    
    def close_dialog(dlg):
        dlg.open = False
        page.update()

    def update_expiration_alert():
        try:
            exp_items = model.get_expiring_products()
            current_count = len(exp_items) if exp_items else 0
            if current_count > 0 and current_count != last_expiring_count[0]:
                snack = ft.SnackBar(
                    content=ft.Row([
                        ft.Icon(ft.Icons.WARNING_ROUNDED, color="white"),
                        ft.Text(f"⚠️ ATENCIÓN: {current_count} productos próximos a vencer. Revise el Dashboard.", color="white", weight="bold"),
                    ]),
                    bgcolor="#D32F2F",
                    duration=5000,
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
            last_expiring_count[0] = current_count
        except Exception as e:
            print(f"Error checking expiration: {e}")

    def refresh_cart():
        cart_list.controls.clear()
        total = 0
        if not cart:
            cart_list.controls.append(ft.Container(content=ft.Text("Carrito vacío\nClick en productos para agregar", size=14, color="grey", text_align=ft.TextAlign.CENTER), alignment=ft.Alignment(0, 0), width=float("inf"), padding=20))
            total_text.value = "Total: $0"
        else:
            subtotal = 0
            for pid, item in cart.items():
                info = item['info']
                qty = item['qty']
                line_total = info[2] * qty
                subtotal += line_total
                cart_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"{info[1]}", size=14, color="black", weight="bold"),
                                ft.Text(f"${info[2]:,.0f} x {int(qty) if qty % 1 == 0 else f'{qty:.3f}'}", size=12, color="grey"),
                            ], expand=True, spacing=2),
                            ft.Text(f"${line_total:,.0f}", size=14, color="green", weight="bold"),
                            ft.TextButton("Eliminar", on_click=lambda e, p=pid: remove_from_cart(p), style=ft.ButtonStyle(color="red"))
                        ], alignment="center"),
                        bgcolor="white", padding=10, border_radius=5, border=ft.border.all(1, "#e0e0e0")
                    )
                )
            discount_pct = current_discount[0]
            discount_amt = subtotal * (discount_pct / 100.0)
            total = subtotal - discount_amt
            if discount_pct > 0:
                 cart_list.controls.append(ft.Divider())
                 cart_list.controls.append(ft.Row([ft.Text("Subtotal:", color="grey"), ft.Text(f"${subtotal:,.0f}", weight="bold")], alignment="spaceBetween"))
                 cart_list.controls.append(ft.Row([ft.Text(f"Descuento ({discount_pct}%):", color="red"), ft.Text(f"-${discount_amt:,.0f}", color="red", weight="bold")], alignment="spaceBetween"))
            total_text.value = f"Total: ${total:,.0f}"
        page.update()

    def remove_from_cart(product_id):
        if product_id in cart:
            del cart[product_id]
        refresh_cart()

    def refresh_products(search_query=""):
        products = model.get_all_products()
        if current_mode == "scanner":
            p_list = list_container.content 
            p_list.controls.clear()
            if search_query:
                products = [p for p in products if search_query.lower() in p[1].lower() or (len(p) >= 6 and p[5] and search_query.lower() in str(p[5]).lower())]
            if not products:
                 p_list.controls.append(ft.Text("Sin resultados"))
            else:
                 for p in products:
                    p_id, p_name, p_price, p_stock, p_crit = p[0], p[1], p[2], p[3], p[4]
                    stock_color = "green" if p_stock > p_crit else "red"
                    p_list.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text(p_name, size=18, weight="bold", color="#1976D2"),
                                ft.Row([ft.Text(f"${p_price:,.0f}", size=16, color="#2E7D32", weight="bold"), ft.Text(f"Stock: {p_stock}", size=14, color=stock_color)], alignment="spaceBetween")
                            ]),
                            bgcolor="white", padding=15, border_radius=10, border=ft.border.all(1, "grey"),
                            on_click=lambda e, pid=p_id, pinfo=p: add_to_cart(pid, pinfo), ink=True
                        )
                    )
        else: # VISUAL MODE (GRID)
            if not grid_container.content:
                 grid_container.content = ft.GridView(expand=True, runs_count=5, max_extent=150, spacing=10, run_spacing=10)
            grid = grid_container.content
            grid.controls.clear()
            if current_category != "Todas":
                products = [p for p in products if (p[6] if len(p) >= 7 else "General") == current_category]
            for p in products:
                p_id, p_name, p_price, p_stock, p_crit = p[0], p[1], p[2], p[3], p[4]
                bg_card = "#2196F3" if p_stock > p_crit else "#F44336"
                grid.controls.append(
                    ft.Container(
                        content=ft.Column([ft.Text(p_name, size=14, weight="bold", color="white", text_align="center", no_wrap=False), ft.Text(f"${p_price:,.0f}", size=12, color="white", weight="bold")], alignment="center", horizontal_alignment="center"),
                        bgcolor=bg_card, padding=10, border_radius=8, alignment=ft.Alignment(0, 0),
                        on_click=lambda e, pid=p_id, pinfo=p: add_to_cart(pid, pinfo), ink=True
                    )
                )
        if page: 
            page.update()
            update_expiration_alert()

    BULK_CATEGORIES = ["Fiambrería", "Verdurería", "Granel"]
    
    def show_bulk_dialog(product_info, on_confirm):
        p_id, p_name, p_price = product_info[0], product_info[1], product_info[2]
        mode_switch = ft.Switch(label="Vender por Precio $ (mil pesos)", value=True)
        input_value = ft.TextField(label="Monto en Pesos ($)", value="", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True, text_size=20, prefix=ft.Text("$"))
        result_preview = ft.Text("Calculando...", size=16, weight="bold")
        
        def update_mode(e):
            if mode_switch.value:
                input_value.label = "Monto en Pesos ($)"; input_value.prefix = ft.Text("$"); input_value.suffix = None
            else:
                input_value.label = "Peso en Gramos"; input_value.prefix = None; input_value.suffix = ft.Text("gr")
            input_value.value = ""; input_value.focus(); result_preview.value = ""; dlg_bulk.update()

        mode_switch.on_change = update_mode
        def calculate_preview(e):
            try:
                val = float(input_value.value)
                if mode_switch.value:
                    kilos = val / p_price; gramos = kilos * 1000; result_preview.value = f"Son: {gramos:,.0f} gramos ({kilos:.3f} Kg)"
                else:
                    kilos = val / 1000.0; total = kilos * p_price; result_preview.value = f"Son: ${total:,.0f} ({kilos:.3f} Kg)"
                result_preview.update()
            except: result_preview.value = ""; result_preview.update()
        input_value.on_change = calculate_preview

        def set_val(val, is_weight=True):
            mode_switch.value = not is_weight; update_mode(None); input_value.value = str(val); calculate_preview(None); dlg_bulk.update()

        def confirm_bulk(e):
            try:
                val = float(input_value.value)
                final_qty = val / p_price if mode_switch.value else val / 1000.0
                if final_qty <= 0: return
                dlg_bulk.open = False; page.update(); on_confirm(final_qty)
            except: pass

        dlg_bulk = ft.AlertDialog(
            title=ft.Text(f"{p_name} (${p_price:,.0f}/Kg)"),
            content=ft.Column([mode_switch, ft.Container(height=10), input_value, result_preview, ft.Divider(), ft.Text("Rápido (Gramos):", size=12, color="grey"), ft.Row([ft.ElevatedButton("1/8 (125g)", on_click=lambda e: set_val(125)), ft.ElevatedButton("1/4 (250g)", on_click=lambda e: set_val(250)), ft.ElevatedButton("1/2 (500g)", on_click=lambda e: set_val(500))], alignment="center")], tight=True, width=400),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_bulk)), ft.FilledButton("Agregar al Carrito", on_click=confirm_bulk)]
        )
        page.overlay.append(dlg_bulk); dlg_bulk.open = True; page.update()

    def add_to_cart(product_id, product_info, quantity=1.0):
        p_cat = product_info[6] if len(product_info) >= 7 and product_info[6] else "General"
        if p_cat in BULK_CATEGORIES and quantity == 1.0:
            show_bulk_dialog(product_info, lambda qty: add_to_cart(product_id, product_info, qty))
            return
        if product_id not in cart: cart[product_id] = {'info': product_info, 'qty': 0.0}
        cart[product_id]['qty'] += quantity
        if cart[product_id]['qty'] > product_info[3]:
             cart[product_id]['qty'] -= quantity
             show_message(page, f"Stock insuficiente (Max: {product_info[3]})", "red")
             return
        refresh_cart()
        qty_msg = f"{int(quantity)}" if quantity.is_integer() else f"{quantity:.3f} Kg"
        show_message(page, f"{product_info[1]} (+{qty_msg})", "green")

    def toggle_mode(e):
        nonlocal current_mode
        if current_mode == "scanner":
            current_mode = "visual"; btn_mode.icon = ft.Icons.LIST; btn_mode.text = "Modo Lista"; search_field.visible = False; category_tabs.visible = True; list_container.visible = False; grid_container.visible = True
        else:
            current_mode = "scanner"; btn_mode.icon = ft.Icons.GRID_VIEW; btn_mode.text = "Modo Visual"; search_field.visible = True; category_tabs.visible = False; list_container.visible = True; grid_container.visible = False
        refresh_products(); page.update()

    def filter_category(e):
        nonlocal current_category; current_category = e.control.data; refresh_products()

    def open_sales_history_dialog(e):
        history_list_dlg = ft.Column(scroll=ft.ScrollMode.AUTO, height=400, spacing=10)
        def refresh_history():
            history_list_dlg.controls.clear()
            recent_sales = model.get_sales_report()[:50]
            if not recent_sales: history_list_dlg.controls.append(ft.Text("No hay ventas recientes.", italic=True))
            for s in recent_sales:
                s_id, s_fecha, s_total, s_medio, s_desc, s_estado = s
                try: hora = s_fecha.split('T')[1][:5]
                except: hora = "--:--"
                history_list_dlg.controls.append(ft.Container(content=ft.Row([ft.Column([ft.Text(f"Ticket #{s_id} - {hora}", weight="bold", color="black"), ft.Text(f"Total: ${s_total:,.0f} ({s_medio})", size=12, color="black")], expand=True, spacing=2), ft.IconButton(icon=ft.Icons.NOT_INTERESTED, icon_color="red", tooltip="Anular Venta", on_click=lambda e, sid=s_id: confirm_void_sale(sid))]), bgcolor="#f5f5f5", padding=15, border_radius=10, border=ft.border.all(1, "#e0e0e0")))
            page.update()
        def confirm_void_sale(sale_id):
            def proceed_void(e):
                success, msg = model.anular_venta(sale_id)
                dlg_confirm.open = False # Cerramos la confirmación
                if success: 
                    show_message(page, msg, "green")
                    dlg_history.open = False # Cerramos el historial
                    refresh_products()
                else: 
                    show_message(page, msg, "red")
                page.update()

            dlg_confirm = ft.AlertDialog(
                title=ft.Text("¿Anular Venta?"), 
                content=ft.Text(f"Se devolverá el stock y se descontará de la caja.\nEsta acción no se puede deshacer."), 
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_confirm)), 
                    ft.ElevatedButton("ANULAR", bgcolor="red", color="white", on_click=proceed_void)
                ]
            )
            page.overlay.append(dlg_confirm); dlg_confirm.open = True; page.update()
        refresh_history()
        dlg_history = ft.AlertDialog(title=ft.Text("Historial de Hoy / Anulaciones"), content=ft.Container(content=history_list_dlg, width=400), actions=[ft.TextButton("Cerrar", on_click=lambda e: close_dialog(dlg_history))])
        page.overlay.append(dlg_history); dlg_history.open = True; page.update()

    def open_discount_dialog():
        dct_field = ft.TextField(label="Porcentaje %", value=str(current_discount[0]), autofocus=True, keyboard_type=ft.KeyboardType.NUMBER)
        def apply_dct(e):
            try:
                val = int(dct_field.value)
                if val < 0 or val > 100: show_message(page, "Debe ser entre 0 y 100", "red"); return
                current_discount[0] = val; refresh_cart(); dlg_dct.open = False; page.update()
            except ValueError: show_message(page, "Valor inválido", "red")
        dlg_dct = ft.AlertDialog(title=ft.Text("Aplicar Descuento"), content=dct_field, actions=[ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_dct)), ft.FilledButton("Aplicar", on_click=apply_dct)])
        page.overlay.append(dlg_dct); dlg_dct.open = True; page.update()

    def checkout(e):
        if not cart: show_message(page, "El carrito está vacío", "orange"); return
        
        dlg_payment = None
        dlg_cash = None

        def finalize_sale(payment_type, client_id=None):
            nonlocal dlg_payment, dlg_cash
            try:
                venta_id = model.register_sale(cart, medio_pago=payment_type, discount_percent=current_discount[0])
                if payment_type == 'DEUDA' and client_id:
                    subtotal = sum(item['qty'] * item['info'][2] for item in cart.values()); total_amount = subtotal - (subtotal * (current_discount[0] / 100.0))
                    model.add_movement(client_id, 'DEUDA', total_amount, f"Compra #{venta_id} (Fiado)", venta_id)
                cart.clear(); current_discount[0] = 0; refresh_cart(); refresh_products()
                
                # Cerrar diálogos si están abiertos
                if dlg_payment: dlg_payment.open = False
                if dlg_cash: dlg_cash.open = False
                
                page.update()
                show_message(page, f"Venta #{venta_id} exitosa", "green")
            except Exception as ex: show_message(page, f"Error: {str(ex)}", "red")

        def show_client_selector():
            nonlocal dlg_payment
            clients = model.get_clients_with_balance(); client_list_view = ft.ListView(expand=True, height=300)
            def finalize_with_client(client_data):
                sub_t = sum(item['qty'] * item['info'][2] for item in cart.values()); current_total = sub_t - (sub_t * (current_discount[0] / 100.0))
                limit = client_data.get('limite', 0); current_balance = client_data.get('saldo_actual', 0)
                if limit > 0 and (current_balance + current_total) > limit:
                    dlg_l = ft.AlertDialog(title=ft.Text("Límite de Crédito Excedido", color="red"), content=ft.Column([ft.Text(f"El cliente {client_data['nombre']} tiene un límite de ${limit:,.0f}."), ft.Text(f"Deuda Actual: ${current_balance:,.0f}"), ft.Text(f"Esta Compra: ${current_total:,.0f}"), ft.Divider(), ft.Text(f"Nuevo Saldo: ${(current_balance+current_total):,.0f}", weight="bold")], tight=True), actions=[ft.TextButton("Entendido", on_click=lambda e: close_dialog(dlg_l))])
                    page.overlay.append(dlg_l); dlg_l.open = True; page.update(); return
                finalize_sale('DEUDA', client_id=client_data['id'])
            def render_list(search_term="", update_ui=True):
                client_list_view.controls.clear(); filtered = [c for c in clients if search_term.lower() in c['nombre'].lower()] if search_term else clients
                for c in filtered: client_list_view.controls.append(ft.ListTile(leading=ft.Icon(ft.Icons.PERSON), title=ft.Text(c['nombre']), subtitle=ft.Text(f"Deuda: ${c['saldo_actual']:,.0f} | Límite: {'$' + format(c['limite'], ',.0f') if c['limite'] > 0 else '∞'}"), on_click=lambda e, cl=c: finalize_with_client(cl)))
                if update_ui: client_list_view.update()
            def show_add_client_form(e):
                name_f = ft.TextField(label="Nombre Completo", autofocus=True); phone_f = ft.TextField(label="Teléfono (Opcional)"); limit_f = ft.TextField(label="Límite de Crédito ($)", value="0", keyboard_type=ft.KeyboardType.NUMBER)
                def save_new_client(e):
                    if not name_f.value: name_f.error_text = "Requerido"; name_f.update(); return
                    try: 
                        new_id = model.add_client(name_f.value, phone_f.value or "", "", float(limit_f.value or 0))
                        show_message(page, "Cliente creado", "green"); show_client_selector()
                    except Exception as ex: show_message(page, f"Error: {ex}", "red")
                dlg_payment.title = ft.Text("Nuevo Cliente"); dlg_payment.content = ft.Column([name_f, phone_f, limit_f, ft.FilledButton("Guardar", on_click=save_new_client, width=float("inf"))], tight=True, width=300); dlg_payment.actions = [ft.TextButton("Volver", on_click=lambda e: show_client_selector())]; page.update()
            s_f = ft.TextField(hint_text="Buscar cliente...", on_change=lambda e: render_list(e.control.value), autofocus=True, prefix_icon=ft.Icons.SEARCH, expand=True)
            render_list(update_ui=False); dlg_payment.title = ft.Text("Selecciona Cliente"); dlg_payment.content = ft.Column([ft.Row([s_f, ft.IconButton(ft.Icons.PERSON_ADD, on_click=show_add_client_form)], alignment="center"), client_list_view], height=400, width=300); dlg_payment.actions = [ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_payment))]; page.update()

        def show_cash_dialog(total_amount):
            nonlocal dlg_cash
            txt_pago = ft.TextField(label="Monto Entregado ($)", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True, text_size=20)
            txt_vuelto = ft.Text("Vuelto: $0", size=20, weight="bold", color="grey")
            def calculate_change(e):
                try:
                    pago = int(txt_pago.value or 0); vuelto = pago - total_amount
                    txt_vuelto.value = f"Vuelto: ${vuelto:,.0f}" if vuelto >= 0 else f"Faltan: ${abs(vuelto):,.0f}"
                    txt_vuelto.color = "green" if vuelto >= 0 else "red"; btn_confirm_cash.disabled = vuelto < 0; dlg_cash.update()
                except: pass
            txt_pago.on_change = calculate_change
            btn_confirm_cash = ft.ElevatedButton("Confirmar Venta", bgcolor="green", color="white", disabled=True, on_click=lambda e: finalize_sale('EFECTIVO'))
            dlg_cash = ft.AlertDialog(title=ft.Text("Pago en Efectivo"), content=ft.Column([ft.Text(f"Total: ${total_amount:,.0f}", size=24, weight="bold"), ft.Divider(), txt_pago, txt_vuelto], tight=True), actions=[ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_cash)), btn_confirm_cash])
            page.overlay.append(dlg_cash); dlg_cash.open = True; page.update()

        def pay_with(method):
            sub_t = sum(item['qty'] * item['info'][2] for item in cart.values()); current_total = sub_t - (sub_t * (current_discount[0] / 100.0))
            if method == "EFECTIVO": show_cash_dialog(current_total)
            elif method == "FIADO": show_client_selector()
            else: finalize_sale(method)

        dlg_payment = ft.AlertDialog(title=ft.Text("Método de Pago"), content=ft.Column([ft.FilledButton("Efectivo", icon=ft.Icons.MONEY, style=ft.ButtonStyle(bgcolor="#4CAF50", color="white"), on_click=lambda e: pay_with("EFECTIVO"), height=50, width=float("inf")), ft.FilledButton("Débito", icon=ft.Icons.CREDIT_CARD, on_click=lambda e: pay_with("DEBITO"), height=50, width=float("inf")), ft.FilledButton("Crédito", icon=ft.Icons.CREDIT_CARD, on_click=lambda e: pay_with("CREDITO"), height=50, width=float("inf")), ft.FilledButton("Transferencia", icon=ft.Icons.QR_CODE, on_click=lambda e: pay_with("TRANSFERENCIA"), height=50, width=float("inf")), ft.Divider(), ft.FilledButton("Fiado", icon=ft.Icons.BOOK, style=ft.ButtonStyle(bgcolor="#D32F2F", color="white"), on_click=lambda e: pay_with("FIADO"), height=50, width=float("inf"))], tight=True, spacing=10), actions=[ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_payment))])
        page.overlay.append(dlg_payment); dlg_payment.open = True; page.update()

    def handle_barcode_scan(e):
        barcode = search_field.value.strip()
        if not barcode: return
        product = model.get_product_by_barcode(barcode)
        if product: add_to_cart(product[0], product); search_field.value = ""; refresh_products(); search_field.update(); show_message(page, f"✓ {product[1]} agregado", "green")
        else: refresh_products(barcode)

    # --- 4. UI CONTROLS INITIALIZATION ---
    search_field = ft.TextField(hint_text="Buscar o escanear...", on_change=lambda e: refresh_products(e.control.value), on_submit=handle_barcode_scan, bgcolor="white", color="black", border_color="#2196F3", height=50, expand=True)
    btn_mode = ft.FilledButton("Modo Visual", icon=ft.Icons.GRID_VIEW, on_click=toggle_mode, style=ft.ButtonStyle(bgcolor="#FF9800", color="white"))
    btn_history = ft.IconButton(icon=ft.Icons.HISTORY, icon_color="white", tooltip="Historial", on_click=open_sales_history_dialog)
    
    cats = ["Todas"] + model.get_all_categories()
    category_tabs = ft.Row(controls=[ft.TextButton(cat, data=cat, on_click=filter_category) for cat in cats], scroll=ft.ScrollMode.AUTO, visible=False)

    # --- 5. LAYOUT ---
    refresh_products()
    refresh_cart()
    
    layout = ft.ResponsiveRow([
        # --- COLUMNA IZQUIERDA (CARRITO) ---
        ft.Container(
            content=ft.Column([
                # HEADER VERDE (AQUÍ ESTÁ EL ARREGLO)
                ft.Container(
                    content=ft.Column([
                        ft.Text("CARRITO", size=24, weight="bold", color="white"), 
                        total_text
                    ], alignment="center", horizontal_alignment="center"), 
                    bgcolor="#4CAF50", 
                    padding=15, 
                    border_radius=ft.border_radius.only(top_left=10, top_right=10),
                    width=float("inf") # <--- ESTO FUERZA A QUE LLENE TODO EL ESPACIO
                ), 
                ft.Container(content=cart_list, padding=5), 
                ft.Divider(height=1, color="grey"), 
                ft.Container(
                    content=ft.Column([
                        ft.Row([ft.OutlinedButton("Descuento %", icon=ft.Icons.DISCOUNT, on_click=lambda e: open_discount_dialog(), expand=True)]), 
                        ft.FilledButton("COBRAR", on_click=checkout, style=ft.ButtonStyle(bgcolor="#4CAF50", color="white"), height=50, expand=True)
                    ], spacing=10, horizontal_alignment="center"), 
                    padding=10
                )
            ], spacing=0), 
            bgcolor="white", 
            border_radius=10, 
            border=ft.border.all(1, "#e0e0e0"), 
            col={"xs": 12, "md": 4}
        ),
        
        # --- COLUMNA DERECHA (PRODUCTOS) ---
        ft.Container(
            content=ft.Column([
                # HEADER AZUL (También le agregamos width=float("inf") por seguridad)
                ft.Container(
                    content=ft.Row([
                        ft.Text("PRODUCTOS", size=20, weight="bold", color="white"), 
                        ft.Row([btn_history, btn_mode], spacing=5)
                    ], alignment="space_between"), 
                    bgcolor="#2196F3", 
                    padding=15, 
                    border_radius=ft.border_radius.only(top_left=10, top_right=10),
                    width=float("inf") # <--- PROTECCIÓN EXTRA AQUÍ TAMBIÉN
                ), 
                ft.Container(
                    content=ft.Column([
                        ft.Row([search_field]), category_tabs
                    ], spacing=10), 
                    padding=10, 
                    bgcolor="white"
                ), 
                ft.Container(
                    content=ft.Column([list_container, grid_container]), 
                    padding=10
                )
            ], spacing=0), 
            bgcolor="white", 
            border_radius=10, 
            border=ft.border.all(1, "#e0e0e0"), 
            col={"xs": 12, "md": 8}
        ),
    ], spacing=10)

    return ft.Column([layout], scroll=ft.ScrollMode.AUTO, expand=True)
