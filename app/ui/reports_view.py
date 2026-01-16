import flet as ft
import datetime
from app.utils.helpers import show_message

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
    
    def refresh_report(e=None):
        s_date = start_date_ref.current.value
        e_date = end_date_ref.current.value
        
        try:
            report = model.get_financial_report(s_date, e_date)
            
            # Actualizar UI
            txt_sales.value = f"${report['total_ventas']:,.0f}"
            txt_expenses.value = f"${report['total_gastos']:,.0f}"
            txt_profit.value = f"${report['utilidad']:,.0f}"
            
            txt_cash_in.value = f"${report['flujo_entradas']:,.0f}" # Caja Real
            txt_credit.value = f"${report['total_fiado']:,.0f}"
            txt_debt_paid.value = f"${report['total_abonos']:,.0f}"
            
            # Color utilidad
            if report['utilidad'] >= 0:
                txt_profit.color = "green"
            else:
                txt_profit.color = "red"
                
            page.update()
            
        except Exception as ex:
            show_message(page, f"Error generando reporte: {ex}", "red")

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
                ft.ElevatedButton("Filtrar", icon=ft.Icons.FILTER_LIST, on_click=refresh_report, bgcolor="#37474F", color="white", height=40),
                col={"xs": 12, "md": 2} # Full width button on mobile
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
            col={"xs": 12, "md": 4} # Mobile: Stacked (12), Desktop: 3 cols (4)
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

    # Initial Load
    # Hack: Wait for build to populate Refs? No, direct access works if we call it after adding to page or manually.
    # We will trigger it via a Timer or just rely on default values showing $0 until user clicks filter.
    # Or better, we call logic directly once to pre-fill.
    
    return ft.Container(
        content=ft.Column([
            ft.Text("La Verdad Financiera", size=24, weight="bold", color="#37474F"),
            ft.Text("Reporte de Desempeño y Flujo de Caja", size=14, color="grey"),
            ft.Divider(),
            filter_bar,
            ft.Divider(height=20, color="transparent"),
            ft.Text("Resumen General", weight="bold"),
            row_1,
            ft.Divider(height=10, color="transparent"),
            ft.Text("Detalle de Flujo de Dinero", weight="bold"),
            row_2,
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
        padding=20,
        expand=True
    )
