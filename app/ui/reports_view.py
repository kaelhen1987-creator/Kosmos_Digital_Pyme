import flet as ft
import datetime
from app.utils.helpers import show_message
from app.utils.formatting import format_currency

def build_reports_view(page: ft.Page, model):
    
    # --- Estado ---
    # Por defecto: Mes actual
    today = datetime.date.today()
    first_day = today.replace(day=1)
    
    start_date_ref = ft.Ref[ft.TextField]()
    end_date_ref = ft.Ref[ft.TextField]()
    
    # Metricas (Refs para actualizar)
    txt_sales = ft.Text("$0", size=20, weight="bold")
    txt_expenses = ft.Text("$0", size=20, weight="bold")
    txt_profit = ft.Text("$0", size=20, weight="bold", color="green")
    
    txt_cash_in = ft.Text("$0", size=16, weight="bold", color="blue")
    txt_credit = ft.Text("$0", size=16, weight="bold", color="orange")
    txt_debt_paid = ft.Text("$0", size=16, weight="bold", color="purple")
    
    # Listas para Top Productos
    top_7_list = ft.Column(spacing=2)
    top_15_list = ft.Column(spacing=2)
    top_30_list = ft.Column(spacing=2)
    
    # Lista para Historial Detallado
    history_list = ft.ListView(expand=True, spacing=5, padding=10)

    # --- DIALOGO DE DETALLES DE VENTA ---
    def show_sale_details(sale_id):
        details = model.get_sale_details(sale_id)
        # details: [(nombre, qty, precio, subtotal), ...]
        
        rows = []
        for d in details:
            rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Container(ft.Text(d[0], text_align="left"), alignment=ft.Alignment(-1, 0), width=120)), # Nombre
                    ft.DataCell(ft.Container(ft.Text(str(d[1]), text_align="center"), alignment=ft.Alignment(0, 0))),      # Cantidad
                    ft.DataCell(ft.Container(ft.Text(format_currency(d[2]), text_align="center"), alignment=ft.Alignment(0, 0))), # Precio
                    ft.DataCell(ft.Container(ft.Text(format_currency(d[3]), text_align="center"), alignment=ft.Alignment(0, 0))), # Subtotal
                ])
            )
            
        dlg_content = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Container(ft.Text("Producto", weight="bold"), alignment=ft.Alignment(-1, 0))),
                ft.DataColumn(ft.Container(ft.Text("Cant", weight="bold"), alignment=ft.Alignment(0, 0))),
                ft.DataColumn(ft.Container(ft.Text("Precio", weight="bold"), alignment=ft.Alignment(0, 0))),
                ft.DataColumn(ft.Container(ft.Text("Subtotal", weight="bold"), alignment=ft.Alignment(0, 0))),
            ],
            rows=rows,
            column_spacing=20,
            heading_row_height=40,
            data_row_min_height=40,
        )

        def close_dialog(dlg):
            dlg.open = False
            page.update()

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


    def refresh_report(e=None):
        s_date = start_date_ref.current.value
        e_date = end_date_ref.current.value
        
        try:
            # 1. Actualizar Métricas
            report = model.get_financial_report(s_date, e_date)
            
            txt_sales.value = f"${report['total_ventas']:,.0f}"
            txt_expenses.value = f"${report['total_gastos']:,.0f}"
            txt_profit.value = f"${report['utilidad']:,.0f}"
            
            txt_cash_in.value = f"${report['flujo_entradas']:,.0f}" # Caja Real
            txt_credit.value = f"${report['total_fiado']:,.0f}"
            txt_debt_paid.value = f"${report['total_abonos']:,.0f}"
            
            if report['utilidad'] >= 0:
                txt_profit.color = "green"
            else:
                txt_profit.color = "red"
                
            
            # 2. Actualizar Top Productos
            def update_top_list(days, container):
                products = model.get_top_selling_products(days=days)
                container.controls.clear()
                if not products:
                    container.controls.append(ft.Text("Sin datos", size=12, color="grey"))
                else:
                    for i, (name, qty) in enumerate(products, 1):
                        container.controls.append(
                            ft.Row([
                                ft.Text(f"{i}. {name}", size=12, expand=True, no_wrap=True, tooltip=name),
                                ft.Text(f"{qty}", size=12, weight="bold")
                            ], alignment="space_between")
                        )
            
            update_top_list(7, top_7_list)
            update_top_list(15, top_15_list)
            update_top_list(30, top_30_list)

            # 3. Actualizar Historial de Ventas
            sales_history = model.get_sales_in_range(s_date, e_date)
            history_list.controls.clear()
            
            if not sales_history:
                history_list.controls.append(ft.Text("No se encontraron ventas en este rango.", color="grey", italic=True))
            else:
                for sale in sales_history:
                    # sale: (id, fecha, total)
                    s_id, s_date_iso, s_total = sale
                    # Formatear fecha y hora
                    date_part = s_date_iso.split('T')[0]
                    time_part = s_date_iso.split('T')[1][:5] if 'T' in s_date_iso else ""
                    
                    history_list.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Row([
                                    ft.Icon(ft.Icons.RECEIPT, color="#2196F3"),
                                    ft.Column([
                                        ft.Text(f"Venta #{s_id}", weight="bold"),
                                        ft.Text(f"{date_part} {time_part}", size=12, color="grey")
                                    ], spacing=2)
                                ]),
                                ft.Row([
                                    ft.Text(f"${s_total:,.0f}", weight="bold", size=16, color="green"),
                                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color="grey"),
                                ])
                            ], alignment="space_between"),
                            bgcolor="white",
                            padding=10,
                            border_radius=8,
                            border=ft.border.all(1, "#f0f0f0"),
                            on_click=lambda e, sid=s_id: show_sale_details(sid),
                            ink=True
                        )
                    )

            page.update()
            
        except Exception as ex:
            show_message(page, f"Error detallando reporte: {ex}", "red")
            print(ex)

    # --- UI Components ---
    
    def date_field(label, value_ref, default_val):
        return ft.TextField(
            ref=value_ref,
            label=label, 
            value=str(default_val), 
            text_size=14,
            height=40,
            content_padding=10,
            on_submit=refresh_report,
            keyboard_type=ft.KeyboardType.DATETIME
        )
    
    filter_bar = ft.Container(
        content=ft.ResponsiveRow([
            ft.Container(date_field("Fecha Inicio", start_date_ref, first_day), col={"xs": 6, "md": 3}),
            ft.Container(date_field("Fecha Fin", end_date_ref, today), col={"xs": 6, "md": 3}),
            ft.Container(
                ft.FilledButton("Filtrar", icon=ft.Icons.FILTER_LIST, on_click=refresh_report, style=ft.ButtonStyle(bgcolor="#37474F", color="white"), height=40),
                col={"xs": 12, "md": 2} 
            )
        ], vertical_alignment=ft.CrossAxisAlignment.END),
        padding=10,
        bgcolor="white",
        border_radius=8
    )
    
    def stat_card(title, control, icon, color):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(icon, color=color), ft.Text(title, color="grey", size=12)]),
                control
            ], spacing=5),
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            col={"xs": 12, "md": 4} 
        )

    # Cards Row 1: The Big Three
    row_1 = ft.ResponsiveRow([
        stat_card("Ventas Brutas", txt_sales, ft.Icons.STORE, "blue"),
        stat_card("Gastos Operativos", txt_expenses, ft.Icons.MONEY_OFF, "red"),
        stat_card("Utilidad (Aprox)", txt_profit, ft.Icons.MONETIZATION_ON, "green"),
    ])
    
    # Cards Row 2: Cash Flow Details
    row_2 = ft.ResponsiveRow([
        stat_card("Dinero REAL en Caja (Entradas)", txt_cash_in, ft.Icons.SAVINGS, "blue"),
        stat_card("Vendido al Fiado (Crédito)", txt_credit, ft.Icons.CREDIT_CARD, "orange"),
        stat_card("Deudas Pagadas (Abonos)", txt_debt_paid, ft.Icons.ASSIGNMENT_RETURN, "purple"),

    ])
    
    # Cards Row 3: Top Products
    def build_top_card(title, content_col, color):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.STAR, size=16, color=color), ft.Text(title, weight="bold", size=14, color=color)]),
                ft.Divider(height=5, color="transparent"),
                ft.Row([
                    ft.Text("Producto", size=12, color="grey", weight="bold", expand=True),
                    ft.Text("Cant.", size=12, color="grey", weight="bold"),
                ]),
                ft.Divider(height=5, color="transparent"),
                content_col
            ]),
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            col={"xs": 12, "md": 4}
        )

    row_top = ft.ResponsiveRow([
        build_top_card("Top 7 Días", top_7_list, "#E91E63"),
        build_top_card("Top 15 Días", top_15_list, "#9C27B0"),
        build_top_card("Top 30 Días", top_30_list, "#673AB7"),
    ])

    # --- CONTENIDO TABS ---
    
    tab_metrics = ft.Container(
        content=ft.Column([
            ft.Text("Resumen General", weight="bold", size=16),
            row_1,
            ft.Divider(height=10, color="transparent"),
            ft.Text("Detalle de Flujo de Dinero", weight="bold", size=16),
            row_2,
            ft.Divider(height=10, color="transparent"),
            ft.Text("Top Productos Más Vendidos", weight="bold", size=16),
            row_top,
             ft.Divider(),
            ft.Container(
                content=ft.Text(
                    "Nota: 'Dinero Real en Caja' considera las ventas en efectivo y los abonos de deudas. "
                    "Descuenta automáticamente lo vendido al fiado.", 
                    size=12, italic=True, color="grey"
                ),
                padding=10
            )
        ], scroll=ft.ScrollMode.AUTO),
        padding=10
    )
    
    tab_history = ft.Container(
        content=ft.Column([
            ft.Text("Listado de Ventas", weight="bold", size=16),
            ft.Text("Haz click en una venta para ver el detalle.", size=12, color="grey"),
            ft.Divider(),
            history_list
        ], scroll=ft.ScrollMode.AUTO, expand=True),
        padding=10,
        expand=True
    )

    # --- TABS MANUAL ---
    
    # Vars
    current_tab = [0] # 0=Metrics, 1=History
    
    content_area = ft.Container(content=tab_metrics, expand=True)
    
    def set_tab(index):
        current_tab[0] = index
        if index == 0:
            content_area.content = tab_metrics
            btn_metrics.style = style_active
            btn_history.style = style_inactive
        else:
            content_area.content = tab_history
            btn_metrics.style = style_inactive
            btn_history.style = style_active
        page.update()
        
    style_active = ft.ButtonStyle(bgcolor="#2196F3", color="white", shape=ft.RoundedRectangleBorder(radius=8))
    style_inactive = ft.ButtonStyle(bgcolor="white", color="#2196F3", shape=ft.RoundedRectangleBorder(radius=8))
    
    btn_metrics = ft.FilledButton(
        "Métricas Financieras", 
        icon=ft.Icons.ANALYTICS, 
        style=style_active,
        on_click=lambda e: set_tab(0),
        expand=True
    )
    
    btn_history = ft.FilledButton(
        "Historial Detallado", 
        icon=ft.Icons.HISTORY, 
        style=style_inactive,
        on_click=lambda e: set_tab(1),
        expand=True
    )
    
    tabs_control = ft.Container(
        content=ft.Column([
            ft.Row([btn_metrics, btn_history], spacing=10),
            ft.Divider(height=10, color="transparent"),
            content_area
        ], expand=True),
        expand=True
    )
    
    return ft.Container(
        content=ft.Column([
            ft.Text("Reportes y Historial", size=24, weight="bold", color="#37474F"),
            ft.Divider(),
            filter_bar,
            ft.Divider(height=10, color="transparent"),
            tabs_control
        ], expand=True),
        padding=20,
        expand=True
    )
