import flet as ft  # pyre-ignore
from app.utils.helpers import is_mobile, show_message  # pyre-ignore

from app.utils.formatting import format_currency  # pyre-ignore

def build_dashboard_view(page: ft.Page, model, on_logout_callback=None):
    from app.utils.theme import theme_manager
    BG = theme_manager.get_color("bg_color")
    SURFACE = theme_manager.get_color("surface")
    BORDER = theme_manager.get_color("border")
    PRIMARY = theme_manager.get_color("primary")
    REVENUE = theme_manager.get_color("revenue")
    EXPENSE = theme_manager.get_color("expense")
    TEXT = theme_manager.get_color("text_primary")
    DIM = theme_manager.get_color("text_secondary")
    FIELD_BG = theme_manager.get_color("field_bg")

    # ==========================
    # 0. LOGICA DE DETALLES (DIALOGOS)
    # ==========================
    def close_dialog(dlg):
        dlg.open = False
        page.update()

    def show_sale_details(sale_id):
        details = model.get_sale_details(sale_id)
        # details: [(nombre, qty, precio, subtotal), ...]
        
        rows = []
        for d in details:
            rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Container(ft.Text(d[0], text_align="left", size=12), alignment=ft.Alignment(-1, 0), width=120)), # Nombre (Left)
                    ft.DataCell(ft.Container(ft.Text(str(d[1]), text_align="center", size=12), alignment=ft.Alignment(0, 0))),      # Cantidad
                    ft.DataCell(ft.Container(ft.Text(format_currency(d[2]), text_align="center", size=12), alignment=ft.Alignment(0, 0))), # Precio
                    # ft.DataCell(ft.Container(ft.Text(format_currency(d[3]), text_align="center"), alignment=ft.Alignment(0, 0))), # Subtotal REMOVIDO
                ])
            )
            
        dlg_content = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Container(ft.Text("Producto", weight="bold", size=12), alignment=ft.Alignment(-1, 0))), # Header Left
                ft.DataColumn(ft.Container(ft.Text("Cant", weight="bold", size=12), alignment=ft.Alignment(0, 0))),
                ft.DataColumn(ft.Container(ft.Text("Precio", weight="bold", size=12), alignment=ft.Alignment(0, 0))),
                # ft.DataColumn(ft.Container(ft.Text("Subtotal", weight="bold"), alignment=ft.Alignment(0, 0))),
            ],
            rows=rows,
            column_spacing=10,
            heading_row_height=40,
            data_row_min_height=40,
            # numeric=False para todos para controlar alineacion manual
        )

        dlg = ft.AlertDialog(
            title=ft.Text(f"Detalle Venta #{sale_id}"),
            content=ft.Column([dlg_content], scroll=ft.ScrollMode.AUTO, height=300),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: close_dialog(dlg))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def show_payment_details(item):
        # item tiene la info necesaria
        # Formatear fecha para que sea legible (sin microsegundos)
        raw_date = item['date']
        try:
            # Intentar parsear ISO format
            import datetime
            dt = datetime.datetime.fromisoformat(raw_date)
            formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_date = raw_date.replace('T', ' ')

        content = ft.Column([
            ft.Text(f"Fecha: {formatted_date}", size=16),
            ft.Text(f"Monto: {format_currency(item['amount'])}", size=20, weight=ft.FontWeight.BOLD, color=REVENUE),
            ft.Divider(),
            ft.Text(f"Info: {item['description']}", size=16),
        ], tight=True)

        dlg = ft.AlertDialog(
            title=ft.Text(f"Detalle de Abono"),
            content=content,
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: close_dialog(dlg))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def show_details(item):
        try:
            if item['type'] == 'VENTA':
                show_sale_details(item['id'])
            else:
                show_payment_details(item)
        except Exception as e:
            print(f"ERROR in show_details: {e}")
            show_message(page, f"Error detallando: {e}", "red")

    # ==========================
    # 1. ESTADO Y CALCULOS
    # ==========================
    
    # Textos de resumen
    txt_total_ventas = ft.Text("$0", size=22, weight="bold", color=PRIMARY)
    txt_total_gastos = ft.Text("$0", size=22, weight="bold", color=EXPENSE)
    txt_ganancia = ft.Text("$0", size=22, weight="bold", color=REVENUE)
    txt_ganancia_margen = ft.Text("0.0% margen", size=11, color=REVENUE)
    txt_transacciones = ft.Text("0", size=22, weight="bold", color=TEXT)
    txt_trans_promedio = ft.Text("prom. $0", size=11, color="grey")
    
    # Listas
    activity_list = ft.ListView(spacing=0, expand=True, padding=0)
    
    # ==========================
    # 2. ALERTA DE VENCIMIENTO
    # ==========================
    expiring_alert = ft.Container(visible=False)

    def show_expiring_details(items):
        # items schema: schema db completa
        # id, nombre, precio, stock, critico, barcode, categoria, vencimiento
        rows = []
        import datetime
        today = datetime.date.today()
        
        for p in items:
            p_name = p[1]
            p_stock = p[3]
            p_exp = p[7] if len(p) >= 8 else "???"
            
            # Calcular dias restantes
            days_left = "--"
            if p_exp:
                try:
                    d_exp = datetime.date.fromisoformat(p_exp)
                    delta = (d_exp - today).days
                    if delta < 0:
                        days_left = f"Venció hace {abs(delta)} días"
                        color = "red"
                    elif delta == 0:
                        days_left = "Vence HOY"
                        color = "red"
                    else:
                        days_left = f"Vence en {delta} días"
                        color = "orange"
                except:
                    days_left = "Fecha inválida"
                    color = "grey"
            else:
                 color = "black"

            rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(p_name, size=12, weight="bold")),
                    ft.DataCell(ft.Text(str(p_stock), size=12)),
                    ft.DataCell(ft.Text(days_left, size=12, color=color)),
                    ft.DataCell(ft.Text(str(p_exp), size=12)),
                ])
            )

        dlg_content = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Producto")),
                ft.DataColumn(ft.Text("Stock")),
                ft.DataColumn(ft.Text("Estado")),
                ft.DataColumn(ft.Text("Fecha")),
            ],
            rows=rows,
            heading_row_height=40,
            data_row_min_height=40,
        )

        dlg = ft.AlertDialog(
            title=ft.Text(f"Productos por Vencer ({len(items)})"),
            content=ft.Column([dlg_content], scroll=ft.ScrollMode.AUTO, height=300),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: close_dialog(dlg))
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def update_expiring_alert(update_ui=True):
        try:
            exp_items = model.get_expiring_products() # items próximos a vencer (7 días)
            
            if exp_items:
                count = len(exp_items)
                expiring_alert.content = ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    width=8, height=8,
                                    bgcolor=EXPENSE,
                                    border_radius=50
                                ),
                                ft.Text(f"{count} productos próximos a vencer", color=EXPENSE, weight="bold", size=13, expand=True),
                            ], spacing=8),
                            expand=True
                        ),
                        ft.OutlinedButton(
                            "Ver detalle",
                            on_click=lambda e: show_expiring_details(exp_items),
                            style=ft.ButtonStyle(
                                side=ft.BorderSide(1, "#F44336"),
                                color=EXPENSE
                            )
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor=SURFACE,
                    padding=ft.padding.symmetric(horizontal=15, vertical=10),
                    border_radius=8,
                    border=ft.border.all(1, "#FFCDD2")
                )
                expiring_alert.visible = True
            else:
                expiring_alert.visible = False
            
            if update_ui:
                expiring_alert.update()
        except Exception as e:
            print(f"Error checking expiration: {e}")

    def refresh_data(initial=False):
        turno = model.get_active_turno()
        if turno:
            _, t_inicio, _, _, _, _ = turno
            fin_report = model.get_financial_report(start_date=t_inicio)
            
            total_s = fin_report["total_ventas"]
            total_e = fin_report["total_gastos"]
            total_a = fin_report.get("total_abonos", 0)
            
            profit = total_s + total_a - total_e
            
            sales = model.get_sales_report() 
            session_sales = [s for s in sales if s[1] >= t_inicio] if sales else []

            payments = model.get_payments_report()
            session_payments = [p for p in payments if p[2] >= t_inicio] if payments else []
            
            expenses = model.get_expenses_report()
            session_expenses = [e for e in expenses if e[3] >= t_inicio] if expenses else []

            tx_count = len(session_sales) + len(session_payments)
            promedio = (total_s + total_a) / tx_count if tx_count > 0 else 0
            margen = (profit / (total_s + total_a) * 100) if (total_s + total_a) > 0 else 0
            
            # Actualizar tarjetas numéricas
            txt_total_ventas.value = f"${total_s + total_a:,.0f}"
            txt_total_gastos.value = f"${total_e:,.0f}"
            txt_ganancia.value = f"${profit:,.0f}"
            txt_ganancia_margen.value = f"{margen:.1f}% margen"
            txt_transacciones.value = str(tx_count)
            txt_trans_promedio.value = f"prom. ${promedio:,.0f}"
            
            if profit >= 0:
                txt_ganancia.color = "#4CAF50"
                txt_ganancia_margen.color = "#4CAF50"
            else:
                txt_ganancia.color = "#F44336"
                txt_ganancia_margen.color = "#F44336"
                
            combined_activity = []
            for s in session_sales:
                combined_activity.append({
                    "id": s[0], "date": s[1], "label": f"Venta #{s[0]}", 
                    "amount": s[2], "color": "#4CAF50", "type": "VENTA", "sign": "+", "description": ""
                })
            for p in session_payments:
                combined_activity.append({
                    "id": p[0], "date": p[2], "label": f"Abono #{p[0]}",  # pyre-ignore
                    "amount": p[4], "color": "#4CAF50", "type": "ABONO", "sign": "+", "description": f"{p[5]}"  # pyre-ignore
                })
            for e in session_expenses:
                combined_activity.append({
                    "id": e[0], "date": e[3], "label": e[1],
                    "amount": e[2], "color": "#F44336", "type": "GASTO", "sign": "-", "description": ""
                })
            
            combined_activity.sort(key=lambda x: x["date"], reverse=True)

            activity_list.controls.clear()
            if not combined_activity:
                 activity_list.controls.append(ft.Container(ft.Text("Sin actividad en esta sesión", color="grey", text_align="center"), padding=20))
            else:
                for item in combined_activity[:50]: 
                    raw_date = item["date"]
                    hora_fmt = raw_date.split('T')[1][:5] if 'T' in raw_date else raw_date
                    
                    activity_list.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(item['label'], size=14, weight="w500", color=TEXT, expand=1),
                                ft.Text(hora_fmt, size=12, color=DIM),
                                ft.Container(width=10),
                                ft.Text(f"{item['sign']}${item['amount']:,.0f}", weight="bold", color=item["color"], width=80, text_align=ft.TextAlign.RIGHT)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=ft.padding.symmetric(vertical=15, horizontal=20),
                            border=ft.border.only(bottom=ft.border.BorderSide(1, BORDER)),
                            on_click=lambda e, it=item: show_details(it) if it["type"] != "GASTO" else None,
                            ink=True if item["type"] != "GASTO" else False
                        )
                    )
        else:
            txt_total_ventas.value = "$0"
            txt_total_gastos.value = "$0"
            txt_ganancia.value = "$0"
            txt_ganancia_margen.value = "0.0% margen"
            txt_transacciones.value = "0"
            txt_trans_promedio.value = "prom. $0"
            
            activity_list.controls.clear()
            activity_list.controls.append(ft.Container(ft.Text("Caja Cerrada. Inicie turno.", color="grey", italic=True, text_align="center"), padding=20))
            
        if not initial:
            page.update()
        
        # Check expirations
        update_expiring_alert(update_ui=not initial)

    # ==========================
    # 2. UI - TARJETAS LATERALES (KPIs)
    # ==========================
    def build_stat_card_vertical(title, value_control, subtitle_control=None):
        content = [
            ft.Text(title, color=DIM, size=13, weight="w400"),
            value_control
        ]
        if subtitle_control:
            content.append(subtitle_control)
            
        return ft.Container(
            content=ft.Column(content, spacing=3),
            bgcolor=SURFACE,
            padding=12,
            border_radius=10,
            width=float("inf"),
        )

    card_sales = build_stat_card_vertical("Ventas", txt_total_ventas)
    card_expenses = build_stat_card_vertical("Gastos", txt_total_gastos)
    card_profit = build_stat_card_vertical("Ganancia", txt_ganancia, txt_ganancia_margen)
    card_tx = build_stat_card_vertical("Transacciones", txt_transacciones, txt_trans_promedio)

    left_column = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("Resumen del día", size=16, weight="bold", color=TEXT),
                padding=ft.padding.only(left=0, top=15, bottom=5)
            ),
            card_sales,
            card_expenses,
            card_profit,
            card_tx
        ], spacing=10),
        width=float("inf")
    )

    # ==========================
    # 3. FORMULARIO DE GASTOS COMPACTO
    # ==========================
    desc_field = ft.TextField(hint_text="Descripción del gasto", bgcolor=SURFACE, filled=True, expand=2, height=40, content_padding=10, text_size=14, hint_style=ft.TextStyle(color="#666666"), color=TEXT, border_color=DIM)
    amount_field = ft.TextField(hint_text="Monto", keyboard_type=ft.KeyboardType.NUMBER, bgcolor=SURFACE, filled=True, expand=1, height=40, content_padding=10, text_size=14, hint_style=ft.TextStyle(color="#666666"), color=TEXT, border_color=DIM)
    
    def add_expense_click(e):
        try:
            desc = desc_field.value.strip()
            if not desc:
                show_message(page, "Ingresa una descripción", "orange")
                return
            monto = float(amount_field.value)
            if monto <= 0:
                show_message(page, "El monto debe ser mayor a 0", "orange")
                return
                
            model.add_expense(desc, monto)
            desc_field.value = ""
            amount_field.value = ""
            refresh_data()
            desc_field.focus()
        except ValueError:
            show_message(page, "Monto inválido", "red")
        except Exception as ex:
            show_message(page, f"Error: {str(ex)}", "red")

    expense_form = ft.Container(
        content=ft.Row([
            desc_field,
            amount_field,
            ft.FilledButton(
                "Registrar", 
                on_click=add_expense_click, 
                style=ft.ButtonStyle(bgcolor=EXPENSE, color="white", shape=ft.RoundedRectangleBorder(radius=5)),
                height=40
            )
        ], spacing=10),
        padding=15,
        border=ft.border.only(top=ft.border.BorderSide(1, "#333333")),
    )

    activity_list.expand = False
    right_column = ft.Container(
        content=ft.Column([
            # Top Header
            ft.Container(
                content=ft.Row([
                    ft.Text("Actividad del día", size=16, weight="bold", color=TEXT, expand=True),
                    ft.Container(
                        content=ft.Text("En vivo", size=12, color=REVENUE, weight="bold"),
                        bgcolor=SURFACE,
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        border_radius=15,
                        border=ft.border.all(1, "#4CAF50")
                    )
                ]),
                padding=ft.padding.only(left=20, right=20, top=15, bottom=5)
            ),
            # List
            ft.Container(content=activity_list, height=360),
            # Form
            expense_form
        ]),
        bgcolor=SURFACE,
        border_radius=10,
    )

    refresh_data(initial=True) # Cargar datos iniciales
    
    return ft.Container(
        content=ft.Column([
            # ALERTA DE VENCIMIENTO
            expiring_alert,
            # Main Layout
            ft.ResponsiveRow([
                ft.Column([left_column], col={"xs": 12, "md": 5, "lg": 3}, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                ft.Column([right_column], col={"xs": 12, "md": 7, "lg": 9}, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
            ], vertical_alignment=ft.CrossAxisAlignment.START, run_spacing=10)
        ], expand=True, scroll=ft.ScrollMode.AUTO),
        expand=True,
        bgcolor=BG,
        padding=20
    )
