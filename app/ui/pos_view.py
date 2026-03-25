import flet as ft  # pyre-ignore
from app.utils.helpers import is_mobile, show_message  # pyre-ignore
from app.utils.printer_helper import generar_ticket_texto, imprimir_ticket  # pyre-ignore

# ── Ya no se usa paleta global estática, se inyecta en la vista ─────────

def build_pos_view(page: ft.Page, model, shared_cart=None):

    from app.utils.theme import theme_manager
    CART_BG  = theme_manager.get_color("surface")
    BG       = theme_manager.get_color("bg_color")
    CARD_BG  = theme_manager.get_color("surface")
    SURFACE  = theme_manager.get_color("surface")
    DIM      = theme_manager.get_color("text_secondary")
    ACCENT   = theme_manager.get_color("nav_bg")
    GREEN    = theme_manager.get_color("revenue")
    BORDER   = theme_manager.get_color("border")
    TEXT     = theme_manager.get_color("text_primary")
    RED      = theme_manager.get_color("expense")
    EXPENSE  = theme_manager.get_color("expense")
    PRIMARY  = theme_manager.get_color("primary")

    # --- 1. STATE VARIABLES ---
    cart = shared_cart if shared_cart is not None else {}
    current_category = ["Todas"]
    current_discount = [0]
    last_expiring_count = [0]

    # --- 2. FORWARD REFS ---
    cart_list      = ft.ListView(spacing=0, expand=True, padding=0)
    cart_count_txt = ft.Text("Carrito · 0 ítems", color=DIM, size=12)
    total_text     = ft.Text("$0", size=32, weight="bold", color=TEXT)
    iva_txt        = ft.Text("IVA incluido (19%)", color=DIM, size=11)

    product_row = ft.Row(wrap=True, spacing=10, run_spacing=10)
    list_container = ft.Container(content=product_row, expand=True)

    # --- 3. HELPERS ---
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
                        ft.Text(f"⚠️  {current_count} productos próximos a vencer.", color="white", weight="bold"),
                    ]),
                    bgcolor=RED, duration=5000,
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
            last_expiring_count[0] = current_count
        except Exception as e:
            print(f"Error checking expiration: {e}")

    # --- 4. CART ---
    def refresh_cart():
        cart_list.controls.clear()
        subtotal = 0
        item_count = 0

        if not cart:
            cart_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.SHOPPING_CART_OUTLINED, color=TEXT, size=40),
                        ft.Text("Carrito vacío", color=DIM, size=13, text_align="center")
                    ], alignment=ft.MainAxisAlignment.CENTER,
                       horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    alignment=ft.Alignment(0.0, 0.0), height=120
                )
            )
        else:
            for pid, item in cart.items():
                info = item['info']
                qty  = item['qty']
                line_total = info[2] * qty
                subtotal  += line_total
                item_count += 1
                qty_str = str(int(qty)) if qty % 1 == 0 else f"{qty:.3f} Kg"

                cart_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(info[1], color=TEXT, size=13, weight="bold",
                                        overflow=ft.TextOverflow.ELLIPSIS, no_wrap=True),
                                ft.Text(f"${info[2]:,.0f} c/u", color=DIM, size=11)
                            ], spacing=2, expand=True),
                            ft.Row([
                                ft.IconButton(ft.Icons.REMOVE, icon_color=DIM, icon_size=16,
                                              style=ft.ButtonStyle(padding=2),
                                              on_click=lambda e, p=pid: _cart_dec(p)),
                                ft.Text(qty_str, color=TEXT, size=13, weight="bold",
                                        width=32, text_align="center"),
                                ft.IconButton(ft.Icons.ADD, icon_color=ACCENT, icon_size=16,
                                              style=ft.ButtonStyle(padding=2),
                                              on_click=lambda e, p=pid, pi=info: add_to_cart(p, pi)),
                            ], spacing=0),
                            ft.Text(f"${line_total:,.0f}", color=GREEN, size=13, weight="bold")
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.symmetric(horizontal=14, vertical=10),
                        border=ft.border.only(bottom=ft.border.BorderSide(1, BORDER))
                    )
                )

            discount_pct = current_discount[0]
            discount_amt = subtotal * (discount_pct / 100.0)
            total = subtotal - discount_amt

            if discount_pct > 0:
                cart_list.controls.append(ft.Container(
                    content=ft.Column([
                        ft.Row([ft.Text("Subtotal:", color=DIM, size=12),
                                ft.Text(f"${subtotal:,.0f}", color=TEXT, size=12)],
                               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([ft.Text(f"Descuento ({discount_pct}%):", color=RED, size=12),
                                ft.Text(f"-${discount_amt:,.0f}", color=RED, size=12, weight="bold")],
                               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ], spacing=4), padding=ft.padding.symmetric(horizontal=14, vertical=8)
                ))
            else:
                total = subtotal

            total_text.value     = f"${total:,.0f}"
            cart_count_txt.value = f"Carrito · {item_count} ítem{'s' if item_count != 1 else ''}"
            page.update()
            return

        total_text.value     = "$0"
        cart_count_txt.value = "Carrito · 0 ítems"
        page.update()

    def _cart_dec(pid):
        if pid in cart:
            cart[pid]['qty'] -= 1
            if cart[pid]['qty'] <= 0:
                del cart[pid]  # pyre-ignore
        refresh_cart()

    def remove_from_cart(product_id):
        if product_id in cart:
            del cart[product_id]  # pyre-ignore
        refresh_cart()

    # --- 5. PRODUCTS ---
    BULK_CATEGORIES = ["Fiambrería", "Verdurería", "Granel"]

    def refresh_products(search_query=""):
        products = model.get_all_products()
        product_row.controls.clear()

        if search_query:
            products = [p for p in products if
                        search_query.lower() in p[1].lower() or # pyre-ignore
                        (len(p) >= 6 and p[5] and search_query.lower() in str(p[5]).lower())]

        cat = current_category[0]
        if cat != "Todas":
            products = [p for p in products if (p[6] if len(p) >= 7 else "General") == cat]  # pyre-ignore

        if not products:
            product_row.controls.append(
                ft.Container(ft.Text("Sin resultados", color=DIM, italic=True),
                             padding=20, alignment=ft.Alignment(0.0, 0.0))
            )
        else:
            for p in products:
                p_id, p_name, p_price = p[0], p[1], p[2]  # pyre-ignore
                p_stock, p_crit       = p[3], p[4]        # pyre-ignore
                p_cat = p[6] if len(p) >= 7 else "General" # pyre-ignore

                is_promo = p_cat == "Promos"
                is_low   = p_stock <= p_crit

                stock_color = "#F44336" if is_low else GREEN
                stock_badge = ft.Container(
                    content=ft.Text(f"{p_stock} ud.", size=10, color="white", weight="bold"),
                    bgcolor=stock_color,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border_radius=10
                )

                if is_promo:
                    card_bg    = SURFACE
                    border_cl  = "#9C27B0"
                    name_color = "#CE93D8"
                    price_color= "#CE93D8"
                    top_label  = ft.Container(
                        content=ft.Text("PROMO", size=9, color="#9C27B0", weight="bold"),
                        padding=ft.padding.symmetric(horizontal=6, vertical=2)
                    )
                else:
                    card_bg    = CARD_BG
                    border_cl  = EXPENSE if is_low else BORDER
                    name_color = TEXT
                    price_color= GREEN
                    top_label  = None

                top_items = [top_label, ft.Container(expand=True), stock_badge] if top_label else [ft.Container(expand=True), stock_badge]

                card = ft.Container(
                    content=ft.Column([
                        ft.Row(top_items, spacing=4),
                        ft.Container(expand=True),
                        ft.Text(p_name, color=name_color, size=13, weight="bold",
                                no_wrap=False, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(f"${p_price:,.0f}", color=price_color, size=15, weight="bold"),
                    ], spacing=3, tight=True),
                    bgcolor=card_bg,
                    border=ft.border.all(1, border_cl),
                    border_radius=10,
                    padding=10,
                    on_click=lambda e, pid=p_id, pinfo=p: add_to_cart(pid, pinfo),
                    ink=True,
                    width=155, height=105
                )
                product_row.controls.append(card)

        if page:
            page.update()
            update_expiration_alert()

    # --- 6. BULK / ADD TO CART ---
    def show_bulk_dialog(product_info, on_confirm):
        p_id, p_name, p_price = product_info[0], product_info[1], product_info[2]
        mode_switch  = ft.Switch(label="Vender por Precio $ (mil pesos)", value=True)
        input_value  = ft.TextField(label="Monto en Pesos ($)", value="", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True, text_size=20, prefix=ft.Text("$"))
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
            content=ft.Column([
                mode_switch, ft.Container(height=10), input_value, result_preview,
                ft.Divider(), ft.Text("Rápido (Gramos):", size=12, color="grey"),
                ft.Row([ft.ElevatedButton("1/8 (125g)", on_click=lambda e: set_val(125)),
                        ft.ElevatedButton("1/4 (250g)", on_click=lambda e: set_val(250)),
                        ft.ElevatedButton("1/2 (500g)", on_click=lambda e: set_val(500))], alignment="center")
            ], tight=True, width=400),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_bulk)),
                     ft.FilledButton("Agregar al Carrito", on_click=confirm_bulk)]
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

    # --- 7. MISC DIALOGS ---
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
                history_list_dlg.controls.append(
                    ft.Container(content=ft.Row([
                        ft.Column([ft.Text(f"Ticket #{s_id} - {hora}", weight="bold", color=TEXT),
                                   ft.Text(f"Total: ${s_total:,.0f} ({s_medio})", size=12, color=TEXT)], expand=True, spacing=2),
                        ft.IconButton(icon=ft.Icons.NOT_INTERESTED, icon_color=RED, tooltip="Anular Venta",
                                      on_click=lambda e, sid=s_id: confirm_void_sale(sid))
                    ]), bgcolor=SURFACE, padding=15, border_radius=10, border=ft.border.all(1, "#e0e0e0"))
                )
            page.update()

        def confirm_void_sale(sale_id):
            def proceed_void(e):
                success, msg = model.anular_venta(sale_id)
                dlg_confirm.open = False
                if success:
                    show_message(page, msg, "green"); dlg_history.open = False; refresh_products()
                else:
                    show_message(page, msg, "red")
                page.update()
            dlg_confirm = ft.AlertDialog(
                title=ft.Text("¿Anular Venta?"),
                content=ft.Text("Se devolverá el stock y se descontará de la caja.\nEsta acción no se puede deshacer."),
                actions=[ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_confirm)),
                         ft.ElevatedButton("ANULAR", bgcolor=RED, color="white", on_click=proceed_void)]
            )
            page.overlay.append(dlg_confirm); dlg_confirm.open = True; page.update()

        refresh_history()
        dlg_history = ft.AlertDialog(
            title=ft.Text("Historial de Hoy / Anulaciones"),
            content=ft.Container(content=history_list_dlg, width=400),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: close_dialog(dlg_history))]
        )
        page.overlay.append(dlg_history); dlg_history.open = True; page.update()

    def open_discount_dialog():
        dct_field = ft.TextField(label="Porcentaje %", value=str(current_discount[0]), autofocus=True, keyboard_type=ft.KeyboardType.NUMBER)
        def apply_dct(e):
            try:
                val = int(dct_field.value)
                if val < 0 or val > 100: show_message(page, "Debe ser entre 0 y 100", "red"); return
                current_discount[0] = val; refresh_cart(); dlg_dct.open = False; page.update()
            except ValueError: show_message(page, "Valor inválido", "red")
        dlg_dct = ft.AlertDialog(title=ft.Text("Aplicar Descuento"), content=dct_field,
                                  actions=[ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_dct)),
                                           ft.FilledButton("Aplicar", on_click=apply_dct)])
        page.overlay.append(dlg_dct); dlg_dct.open = True; page.update()

    # --- 8. CHECKOUT ---
    def checkout(e):
        if not cart: show_message(page, "El carrito está vacío", "orange"); return
        dlg_payment = None; dlg_cash = None

        def finalize_sale(payment_type, client_id=None):
            nonlocal dlg_payment, dlg_cash
            try:
                venta_id = model.register_sale(cart, medio_pago=payment_type, discount_percent=current_discount[0])
                if payment_type == 'DEUDA' and client_id:
                    subtotal = sum(item['qty'] * item['info'][2] for item in cart.values())
                    total_amount = subtotal - (subtotal * (current_discount[0] / 100.0))
                    model.add_movement(client_id, 'DEUDA', total_amount, f"Compra #{venta_id} (Fiado)", venta_id)
                subtotal_v = sum(item['qty'] * item['info'][2] for item in cart.values())
                total_v    = subtotal_v - (subtotal_v * (current_discount[0] / 100.0))
                try:
                    texto = generar_ticket_texto(
                        venta_id=venta_id, carrito=cart, total=total_v, medio_pago=payment_type,
                        descuento=current_discount[0],
                        nombre_local=model.get_config("business_name", "MI NEGOCIO"),
                        rut_local=model.get_config("business_rut", ""),
                        direccion_local=model.get_config("business_address", ""),
                        telefono_local=model.get_config("business_phone", ""),
                        tipo_impresora=model.get_config("tipo_impresora", "58mm"),
                        mensaje_pie=model.get_config("ticket_mensaje", "¡Gracias por su preferencia!")
                    )
                    ok = imprimir_ticket(texto)
                    print_msg = ("🖨️  Ticket enviado a impresora", "#1565C0") if ok else ("⚠️  Venta OK, impresora no respondió", "#E65100")
                except Exception as pe:
                    print(f"[POS] Error al imprimir: {pe}"); print_msg = ("⚠️  Venta OK, impresora no respondió", "#E65100")
                cart.clear(); current_discount[0] = 0; refresh_cart(); refresh_products()
                if dlg_payment: dlg_payment.open = False  # pyre-ignore
                if dlg_cash:    dlg_cash.open = False     # pyre-ignore
                page.update()
                show_message(page, f"✅  Venta #{venta_id} registrada", "green")
                show_message(page, print_msg[0], print_msg[1])
            except Exception as ex: show_message(page, f"Error: {str(ex)}", "red")

        def show_client_selector():
            nonlocal dlg_payment
            clients = model.get_clients_with_balance()
            client_list_view = ft.ListView(expand=True, height=300)
            def finalize_with_client(client_data):
                sub_t = sum(item['qty'] * item['info'][2] for item in cart.values())
                current_total = sub_t - (sub_t * (current_discount[0] / 100.0))
                limit = client_data.get('limite', 0); current_balance = client_data.get('saldo_actual', 0)
                if limit > 0 and (current_balance + current_total) > limit:
                    dlg_l = ft.AlertDialog(
                        title=ft.Text("Límite de Crédito Excedido", color=RED),
                        content=ft.Column([ft.Text(f"Cliente: {client_data['nombre']}"),
                                           ft.Text(f"Límite: ${limit:,.0f}"),
                                           ft.Text(f"Deuda actual: ${current_balance:,.0f}"),
                                           ft.Text(f"Esta compra: ${current_total:,.0f}"),
                                           ft.Text(f"Nuevo saldo: ${(current_balance+current_total):,.0f}", weight="bold")], tight=True),
                        actions=[ft.TextButton("Entendido", on_click=lambda e: close_dialog(dlg_l))]
                    )
                    page.overlay.append(dlg_l); dlg_l.open = True; page.update(); return
                finalize_sale('DEUDA', client_id=client_data['id'])

            def render_list(search_term="", update_ui=True):
                client_list_view.controls.clear()
                filtered = [c for c in clients if search_term.lower() in c['nombre'].lower()] if search_term else clients
                for c in filtered:
                    client_list_view.controls.append(
                        ft.ListTile(leading=ft.Icon(ft.Icons.PERSON), title=ft.Text(c['nombre']),
                                    subtitle=ft.Text(f"Deuda: ${c['saldo_actual']:,.0f} | Límite: {'$' + format(c['limite'], ',.0f') if c['limite'] > 0 else '∞'}"),
                                    on_click=lambda e, cl=c: finalize_with_client(cl))
                    )
                if update_ui: client_list_view.update()

            def show_add_client_form(e):
                name_f = ft.TextField(label="Nombre Completo", autofocus=True)
                phone_f = ft.TextField(label="Teléfono (Opcional)")
                limit_f = ft.TextField(label="Límite de Crédito ($)", value="0", keyboard_type=ft.KeyboardType.NUMBER)
                def save_new_client(e):
                    if not name_f.value: name_f.error_text = "Requerido"; name_f.update(); return
                    try:
                        model.add_client(name_f.value, phone_f.value or "", "", float(limit_f.value or 0))
                        show_message(page, "Cliente creado", "green"); show_client_selector()
                    except Exception as ex: show_message(page, f"Error: {ex}", "red")
                dlg_payment.title = ft.Text("Nuevo Cliente")  # pyre-ignore
                dlg_payment.content = ft.Column([name_f, phone_f, limit_f, ft.FilledButton("Guardar", on_click=save_new_client, width=float("inf"))], tight=True, width=300) # pyre-ignore
                dlg_payment.actions = [ft.TextButton("Volver", on_click=lambda e: show_client_selector())] # pyre-ignore
                page.update()

            s_f = ft.TextField(hint_text="Buscar cliente...", on_change=lambda e: render_list(e.control.value), autofocus=True, prefix_icon=ft.Icons.SEARCH, expand=True)
            render_list(update_ui=False)
            dlg_payment.title = ft.Text("Selecciona Cliente")  # pyre-ignore
            dlg_payment.content = ft.Column([ft.Row([s_f, ft.IconButton(ft.Icons.PERSON_ADD, on_click=show_add_client_form)], alignment="center"), client_list_view], height=400, width=300) # pyre-ignore
            dlg_payment.actions = [ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_payment))] # pyre-ignore
            page.update()

        def show_cash_dialog(total_amount):
            nonlocal dlg_cash
            txt_pago = ft.TextField(
                label="Monto Entregado ($)", value=str(int(total_amount)),
                keyboard_type=ft.KeyboardType.NUMBER, autofocus=True, text_size=20,
                on_submit=lambda e: finalize_sale('EFECTIVO') if not btn_confirm_cash.disabled else None
            )
            txt_vuelto = ft.Text("Vuelto: $0", size=20, weight="bold", color=GREEN)
            def calculate_change(e):
                try:
                    pago = int(txt_pago.value or 0); vuelto = pago - total_amount
                    txt_vuelto.value = f"Vuelto: ${vuelto:,.0f}" if vuelto >= 0 else f"Faltan: ${abs(vuelto):,.0f}"
                    txt_vuelto.color = "green" if vuelto >= 0 else "red"
                    btn_confirm_cash.disabled = (vuelto < 0)
                    txt_vuelto.update(); btn_confirm_cash.update()
                except: pass
            txt_pago.on_change = calculate_change
            btn_confirm_cash = ft.ElevatedButton("Confirmar Venta", bgcolor=GREEN, color="white", disabled=False, on_click=lambda e: finalize_sale('EFECTIVO'))
            dlg_cash = ft.AlertDialog(
                title=ft.Text("Pago en Efectivo"),
                content=ft.Column([ft.Text(f"Total a Pagar: ${total_amount:,.0f}", size=24, weight="bold"), ft.Divider(), txt_pago, txt_vuelto], tight=True),
                actions=[ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_cash)), btn_confirm_cash]
            )
            page.overlay.append(dlg_cash); dlg_cash.open = True; page.update()

        def pay_with(method):
            sub_t = sum(item['qty'] * item['info'][2] for item in cart.values())
            current_total = sub_t - (sub_t * (current_discount[0] / 100.0))
            if method == "EFECTIVO": show_cash_dialog(current_total)
            elif method == "FIADO": show_client_selector()
            else: finalize_sale(method)

        dlg_payment = ft.AlertDialog(
            title=ft.Text("Método de Pago"),
            content=ft.Column([
                ft.FilledButton("Efectivo", icon=ft.Icons.MONEY, style=ft.ButtonStyle(bgcolor=PRIMARY, color="white"), on_click=lambda e: pay_with("EFECTIVO"), height=50, width=float("inf")),
                ft.FilledButton("Débito", icon=ft.Icons.CREDIT_CARD, on_click=lambda e: pay_with("DEBITO"), height=50, width=float("inf")),
                ft.FilledButton("Crédito", icon=ft.Icons.CREDIT_CARD, on_click=lambda e: pay_with("CREDITO"), height=50, width=float("inf")),
                ft.FilledButton("Transferencia", icon=ft.Icons.QR_CODE, on_click=lambda e: pay_with("TRANSFERENCIA"), height=50, width=float("inf")),
                ft.Divider(),
                ft.FilledButton("Fiado", icon=ft.Icons.BOOK, style=ft.ButtonStyle(bgcolor=RED, color="white"), on_click=lambda e: pay_with("FIADO"), height=50, width=float("inf")),
            ], tight=True, spacing=10),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_payment))]
        )
        page.overlay.append(dlg_payment); dlg_payment.open = True; page.update()

    # --- 9. BARCODE ---
    def handle_barcode_scan(e=None):
        barcode = search_field.value.strip()
        if not barcode: return
        product = model.get_product_by_barcode(barcode)
        if product:
            add_to_cart(product[0], product); search_field.value = ""; refresh_products(); search_field.update()
            show_message(page, f"✓ {product[1]} agregado", "green")
        else:
            refresh_products(barcode)

    # --- 10. UI COMPONENTS ---
    search_field = ft.TextField(
        hint_text="Buscar producto o escanear código de barras...",
        hint_style=ft.TextStyle(color="#555555"),
        on_change=lambda e: refresh_products(e.control.value),
        on_submit=handle_barcode_scan,
        bgcolor=BG, color=TEXT,
        border_color=ACCENT, focused_border_color=ACCENT,
        height=52, expand=True,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
        text_size=16, prefix_icon=ft.Icons.SEARCH, autofocus=True
    )

    cats = ["Todas"] + model.get_all_categories()
    active_chip_style = ft.ButtonStyle(
        bgcolor=ACCENT, color="white",
        shape=ft.RoundedRectangleBorder(radius=20),
        padding=ft.padding.symmetric(horizontal=14, vertical=6)
    )
    inactive_chip_style = ft.ButtonStyle(
        bgcolor=SURFACE, color=DIM,
        shape=ft.RoundedRectangleBorder(radius=20),
        padding=ft.padding.symmetric(horizontal=14, vertical=6)
    )
    cat_buttons = []

    def filter_category_ui(e):
        current_category[0] = e.control.data
        for btn in cat_buttons:
            btn.style = active_chip_style if btn.data == current_category[0] else inactive_chip_style
        refresh_products()
        page.update()

    for cat in cats:
        btn = ft.TextButton(
            cat, data=cat,
            style=active_chip_style if cat == "Todas" else inactive_chip_style,
            on_click=filter_category_ui
        )
        cat_buttons.append(btn)

    category_row = ft.Row(controls=cat_buttons, scroll=ft.ScrollMode.AUTO)

    refresh_products()
    refresh_cart()

    # --- 11. LAYOUT ---
    return ft.Container(
        content=ft.Row([
            # ── PRODUCTOS (izquierda, expansible) ──────────────────
            ft.Container(
                content=ft.Column([
                    # Scanner prominente
                    ft.Row([
                        search_field,
                        ft.FilledButton(
                            "Escanear",
                            icon=ft.Icons.QR_CODE_SCANNER,
                            style=ft.ButtonStyle(bgcolor=ACCENT, color="white", shape=ft.RoundedRectangleBorder(radius=10)),
                            height=52, on_click=handle_barcode_scan
                        )
                    ], spacing=10),
                    # Chips de categoría
                    ft.Container(content=category_row, padding=ft.padding.symmetric(vertical=6)),
                    # Grid de tarjetas
                    ft.Container(
                        content=ft.ListView(controls=[list_container], expand=True, spacing=0, padding=0),
                        expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE
                    )
                ], expand=True, spacing=0),
                expand=True, padding=20, bgcolor=BG
            ),

            # ── CARRITO (derecha, fijo 300px) ──────────────────────
            ft.Container(
                content=ft.Column([
                    # Header
                    ft.Container(
                        content=ft.Column([cart_count_txt, total_text, iva_txt], spacing=2),
                        padding=ft.padding.symmetric(horizontal=20, vertical=16),
                        border=ft.border.only(bottom=ft.border.BorderSide(1, BORDER))
                    ),
                    # Lista items (scrollable)
                    ft.Container(content=cart_list, expand=True),
                    # Acciones
                    ft.Container(
                        content=ft.Column([
                            ft.OutlinedButton(
                                "Descuento %",
                                style=ft.ButtonStyle(side=ft.BorderSide(1, "#333333"), color=DIM, shape=ft.RoundedRectangleBorder(radius=8)),
                                width=float("inf"), height=40,
                                on_click=lambda e: open_discount_dialog()
                            ),
                            ft.FilledButton(
                                "COBRAR",
                                style=ft.ButtonStyle(bgcolor=PRIMARY, color="white", shape=ft.RoundedRectangleBorder(radius=10)),
                                width=float("inf"), height=54,
                                on_click=checkout
                            ),
                            ft.TextButton(
                                "Anular venta",
                                style=ft.ButtonStyle(color=DIM),
                                width=float("inf"), height=36,
                                on_click=open_sales_history_dialog
                            ),
                        ], spacing=8),
                        padding=ft.padding.symmetric(horizontal=16, vertical=12),
                        border=ft.border.only(top=ft.border.BorderSide(1, BORDER))
                    )
                ], spacing=0, expand=True),
                bgcolor=CART_BG,
                border=ft.border.all(1, BORDER),
                border_radius=ft.border_radius.only(top_right=12, bottom_right=12),
                width=300
            ),
        ], spacing=0, expand=True),
        expand=True, bgcolor=BG
    )
