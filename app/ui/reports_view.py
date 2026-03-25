import flet as ft
import datetime
import os
from app.utils.helpers import show_message
from app.utils.formatting import format_currency
from app.utils.pdf_exporter import generate_report_pdf

# Tema oscuro
def build_reports_view(page: ft.Page, model):
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


    today = datetime.date.today()
    first_day = today.replace(day=1)

    start_date_ref = ft.Ref[ft.TextField]()
    end_date_ref   = ft.Ref[ft.TextField]()

    # ── Estado compartido (valores, no controles) ──────────────────────
    _data = {
        "ventas": 0, "gastos": 0, "utilidad": 0, "margen": 0.0,
        "tx_count": 0, "exp_count": 0,
        "cash_in": 0, "credit": 0, "abonos": 0,
    }

    # ── Controles de métricas (cada sección tiene los suyos) ───────────
    def mk_txt(v="$0", size=22, color=TEXT, bold=True):
        return ft.Text(v, size=size, weight="bold" if bold else "normal", color=color)

    # Sección 0 – Métricas generales
    m_ventas    = mk_txt(color=PRIMARY)
    m_gastos    = mk_txt(color=EXPENSE)
    m_profit    = mk_txt(color=REVENUE)
    m_tx_lbl    = ft.Text("0 transacciones", size=12, color=DIM)
    m_exp_lbl   = ft.Text("0 egresos", size=12, color=DIM)
    m_margin    = ft.Text("0% margen", size=12, color=REVENUE)
    m_cash_in   = mk_txt(color=TEXT)
    m_credit    = mk_txt(color="#FF9800")
    m_abonos    = mk_txt(color=REVENUE)

    # Sección 1 – Flujo de caja (controles SEPARADOS para evitar doble padre)
    f_cash_in   = mk_txt(color=TEXT)
    f_credit    = mk_txt(color="#FF9800")
    f_abonos    = mk_txt(color=REVENUE)

    # Top productos
    top_7_list  = ft.Column(spacing=4)
    top_15_list = ft.Column(spacing=4)
    top_30_list = ft.Column(spacing=4)

    # Listas historial
    history_sales_list    = ft.ListView(expand=True, spacing=0, padding=0)
    history_expenses_list = ft.ListView(expand=True, spacing=0, padding=0)
    history_fiados_list   = ft.ListView(expand=True, spacing=0, padding=0)

    # ── Detalle de venta ───────────────────────────────────────────────
    def show_sale_details(sale_id):
        details = model.get_sale_details(sale_id)
        rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(d[0], size=12, color=TEXT)),
                ft.DataCell(ft.Text(str(d[1]), size=12, color=TEXT)),
                ft.DataCell(ft.Text(format_currency(d[2]), size=12, color=TEXT)),
            ])
            for d in details
        ]
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Producto", weight="bold", size=12, color=DIM)),
                ft.DataColumn(ft.Text("Cant.", weight="bold", size=12, color=DIM)),
                ft.DataColumn(ft.Text("Precio", weight="bold", size=12, color=DIM)),
            ],
            rows=rows, column_spacing=20, heading_row_height=36, data_row_min_height=36,
        )
        dlg = ft.AlertDialog(
            title=ft.Text(f"Detalle Venta #{sale_id}", color=TEXT),
            content=ft.Container(
                content=ft.Column([table], scroll=ft.ScrollMode.AUTO, height=300),
                bgcolor=SURFACE, padding=10, border_radius=8,
            ),
            bgcolor=SURFACE,
            actions=[ft.TextButton("Cerrar", on_click=lambda e: _close(dlg))],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def _close(dlg):
        dlg.open = False
        page.update()

    # ── Exportar PDF ───────────────────────────────────────────────────
    def export_pdf():
        s_date = start_date_ref.current.value
        e_date = end_date_ref.current.value
        try:
            report  = model.get_financial_report(s_date, e_date)
            sales   = model.get_sales_in_range(s_date, e_date)
            tops    = model.get_top_selling_products(days=30)
            clients_debt = [c for c in model.get_clients_with_balance() if c['saldo_actual'] > 0]

            if hasattr(model, 'get_expenses_in_range'):
                expenses = model.get_expenses_in_range(s_date, e_date)
            else:
                all_exp = model.get_expenses_report() or []
                expenses = [ex for ex in all_exp if s_date <= (ex[3].split('T')[0] if 'T' in ex[3] else ex[3]) <= e_date]

            report_data = {
                "start_date": s_date,
                "end_date":   e_date,
                "total_ventas":   report.get("total_ventas", 0),
                "total_gastos":   report.get("total_gastos", 0),
                "utilidad":       report.get("utilidad", 0),
                "flujo_entradas": report.get("flujo_entradas", 0),
                "total_fiado":    report.get("total_fiado", 0),
                "total_abonos":   report.get("total_abonos", 0),
                "tx_count":       len(sales),
                "exp_count":      len(expenses),
                "top_products":   tops,
                "sales_history":  sales,
                "expenses_history": expenses,
                "clients_debt":   clients_debt,
            }

            docs_dir = os.path.expanduser("~/Documents/Digital_PyME")
            os.makedirs(docs_dir, exist_ok=True)
            filename = f"reporte_{s_date}_{e_date}.pdf"
            out_path = os.path.join(docs_dir, filename)

            generate_report_pdf(report_data, out_path)
            show_message(page, f"PDF guardado en: {out_path}", "green")

            # Abrir el archivo automáticamente
            import subprocess
            subprocess.Popen(["open", out_path])

        except Exception as ex:
            show_message(page, f"Error al generar PDF: {ex}", "red")
            import traceback; traceback.print_exc()

    # ── Refresh principal ──────────────────────────────────────────────
    def refresh_report(e=None):
        s_date = start_date_ref.current.value
        e_date = end_date_ref.current.value
        try:
            report  = model.get_financial_report(s_date, e_date)
            ventas  = report['total_ventas']
            gastos  = report['total_gastos']
            util    = report['utilidad']
            abonos  = report.get('total_abonos', 0)
            fiado   = report.get('total_fiado', 0)
            entradas= report.get('flujo_entradas', 0)
            pct     = (util / ventas * 100) if ventas > 0 else 0

            # Actualizar sección Métricas
            m_ventas.value  = f"${ventas:,.0f}"
            m_gastos.value  = f"${gastos:,.0f}"
            m_profit.value  = f"${util:,.0f}"
            m_profit.color  = "#4CAF50" if util >= 0 else "#F44336"
            m_margin.value  = f"{pct:.1f}% margen"
            m_margin.color  = "#4CAF50" if util >= 0 else "#F44336"
            m_cash_in.value = f"${entradas:,.0f}"
            m_credit.value  = f"${fiado:,.0f}"
            m_abonos.value  = f"${abonos:,.0f}"

            # Actualizar sección Flujo
            f_cash_in.value = f"${entradas:,.0f}"
            f_credit.value  = f"${fiado:,.0f}"
            f_abonos.value  = f"${abonos:,.0f}"

            # ── Historial ventas ───────────────────────────────────────
            sales_history = model.get_sales_in_range(s_date, e_date)
            m_tx_lbl.value = f"{len(sales_history)} transacciones"
            history_sales_list.controls.clear()

            if not sales_history:
                history_sales_list.controls.append(
                    ft.Container(ft.Text("Sin ventas en este período.", color=DIM, italic=True), padding=20)
                )
            else:
                for sale in sales_history:
                    s_id = sale[0]; s_date_val = sale[1]; s_total = sale[2]
                    s_pago = (sale[3] if len(sale) >= 4 else None) or "EFECTIVO"
                    dp = s_date_val.split('T')[0]
                    tp = s_date_val.split('T')[1][:5] if 'T' in s_date_val else ""
                    pc = {"EFECTIVO":"#4CAF50","TRANSFERENCIA":"#2196F3",
                          "DEBITO":"#9C27B0","CREDITO":"#9C27B0","DEUDA":"#FF9800"}.get(s_pago,"#4CAF50")
                    history_sales_list.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(f"Venta #{s_id}", weight="bold", color=TEXT, size=14),
                                    ft.Text(f"{dp} {tp}", size=11, color=DIM)
                                ], spacing=2, expand=True),
                                ft.Column([
                                    ft.Text(f"${s_total:,.0f}", weight="bold", color=REVENUE, size=15),
                                    ft.Container(
                                        ft.Text(s_pago, size=10, color=pc, weight="bold"),
                                        bgcolor=ft.Colors.with_opacity(0.12, pc),
                                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                        border_radius=10
                                    )
                                ], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.END),
                                ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#555555", size=18)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=ft.padding.symmetric(horizontal=20, vertical=14),
                            border=ft.border.only(bottom=ft.border.BorderSide(1, BORDER)),
                            on_click=lambda e, sid=s_id: show_sale_details(sid), ink=True
                        )
                    )

            # ── Historial gastos ───────────────────────────────────────
            # Intentar filtro por rango, si no existe tomar todos
            if hasattr(model, 'get_expenses_in_range'):
                expenses = model.get_expenses_in_range(s_date, e_date)
            else:
                all_exp = model.get_expenses_report() or []
                expenses = [ex for ex in all_exp if s_date <= (ex[3].split('T')[0] if 'T' in ex[3] else ex[3]) <= e_date]

            m_exp_lbl.value = f"{len(expenses)} egresos"
            history_expenses_list.controls.clear()

            if not expenses:
                history_expenses_list.controls.append(
                    ft.Container(ft.Text("Sin gastos en este período.", color=DIM, italic=True), padding=20)
                )
            else:
                for exp in expenses:
                    e_id, e_desc, e_monto, e_fecha = exp[0], exp[1], exp[2], exp[3]
                    dp = e_fecha.split('T')[0] if 'T' in e_fecha else e_fecha
                    history_expenses_list.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(e_desc, weight="bold", color=TEXT, size=14),
                                    ft.Text(dp, size=11, color=DIM)
                                ], spacing=2, expand=True),
                                ft.Text(f"-${e_monto:,.0f}", weight="bold", color=EXPENSE, size=15)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=ft.padding.symmetric(horizontal=20, vertical=14),
                            border=ft.border.only(bottom=ft.border.BorderSide(1, BORDER)),
                        )
                    )

            # ── Fiados pendientes ──────────────────────────────────────
            clients_debt = [c for c in model.get_clients_with_balance() if c['saldo_actual'] > 0]
            history_fiados_list.controls.clear()
            if not clients_debt:
                history_fiados_list.controls.append(
                    ft.Container(ft.Text("Sin fiados pendientes.", color=DIM, italic=True), padding=20)
                )
            else:
                for c in clients_debt:
                    history_fiados_list.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(c['nombre'], weight="bold", color=TEXT, size=14),
                                    ft.Text(c['alias'] if c['alias'] else "Sin alias", color=DIM, size=11)
                                ], spacing=2, expand=True),
                                ft.Text(f"${c['saldo_actual']:,.0f}", weight="bold", color="#FF9800", size=15)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=ft.padding.symmetric(horizontal=20, vertical=14),
                            border=ft.border.only(bottom=ft.border.BorderSide(1, BORDER)),
                        )
                    )

            # ── Top productos ──────────────────────────────────────────
            def upd_top(days, col):
                products = model.get_top_selling_products(days=days)
                col.controls.clear()
                col.controls.append(ft.Row([
                    ft.Text("Producto", size=11, color=DIM, weight="bold", expand=True),
                    ft.Text("Cant.", size=11, color=DIM, weight="bold")
                ]))
                if not products:
                    col.controls.append(ft.Text("Sin datos", size=12, color=DIM))
                else:
                    for i, (name, qty) in enumerate(products, 1):
                        col.controls.append(ft.Container(
                            content=ft.Row([
                                ft.Text(f"{i}. {name}", size=13, color=TEXT, expand=True,
                                        no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(str(qty), size=13, color=REVENUE, weight="bold")
                            ]),
                            padding=ft.padding.symmetric(vertical=8),
                            border=ft.border.only(bottom=ft.border.BorderSide(1, BORDER))
                        ))

            upd_top(7,  top_7_list)
            upd_top(15, top_15_list)
            upd_top(30, top_30_list)

            page.update()
        except Exception as ex:
            show_message(page, f"Error: {ex}", "red")
            import traceback; traceback.print_exc()

    # ── Helpers UI ────────────────────────────────────────────────────
    def dcard(title, val_ctrl, sub_ctrl=None):
        col = [ft.Text(title, color=DIM, size=13), val_ctrl]
        if sub_ctrl: col.append(sub_ctrl)
        return ft.Container(
            content=ft.Column(col, spacing=4),
            bgcolor=SURFACE, padding=16, border_radius=10,
            border=ft.border.all(1, BORDER), expand=True
        )

    note = ft.Text(
        "Nota: \"Efectivo real\" considera ventas en efectivo + abonos, descontando ventas al fiado.",
        size=11, italic=True, color=DIM
    )
    note2 = ft.Text(
        "El flujo de caja separa ingresos reales de las ventas al crédito.",
        size=11, italic=True, color=DIM
    )

    def top_block(title, lst, color):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.STAR, size=14, color=color), ft.Text(title, color=color, size=14, weight="bold")]),
                ft.Container(height=8),
                lst
            ], spacing=0, tight=True),
            bgcolor=SURFACE, padding=16, border_radius=10, expand=True
        )

    def list_section(title, lst_ctrl):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=16, weight="bold", color=TEXT),
                ft.Container(height=5),
                ft.Container(
                    content=lst_ctrl, expand=True,
                    bgcolor=SURFACE, border_radius=10,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE
                )
            ], expand=True),
            expand=True
        )

    # ── Secciones (cada una con sus propios controles) ────────────────
    sections_map = {
        0: ft.Container(
            content=ft.Column([
                ft.Text("Métricas generales", size=16, weight="bold", color=TEXT),
                ft.Container(height=10),
                ft.Row([dcard("Ventas brutas", m_ventas, m_tx_lbl),
                        dcard("Gastos operativos", m_gastos, m_exp_lbl),
                        dcard("Utilidad aprox.", m_profit, m_margin)], spacing=10),
                ft.Container(height=10),
                ft.Row([dcard("Efectivo en caja", m_cash_in),
                        dcard("Al fiado (crédito)", m_credit),
                        dcard("Abonos recibidos", m_abonos)], spacing=10),
                ft.Container(height=15),
                note
            ], scroll=ft.ScrollMode.AUTO),
            expand=True
        ),
        1: ft.Container(
            content=ft.Column([
                ft.Text("Flujo de caja", size=16, weight="bold", color=TEXT),
                ft.Container(height=10),
                ft.Row([dcard("Efectivo en caja", f_cash_in),
                        dcard("Al fiado (crédito)", f_credit),
                        dcard("Abonos recibidos", f_abonos)], spacing=10),
                ft.Container(height=15),
                note2
            ], scroll=ft.ScrollMode.AUTO),
            expand=True
        ),
        2: ft.Container(
            content=ft.Column([
                ft.Text("Top productos", size=16, weight="bold", color=TEXT),
                ft.Container(height=10),
                ft.Row([
                    top_block("Top 7 Días",  top_7_list,  "#E91E63"),
                    top_block("Top 15 Días", top_15_list, "#9C27B0"),
                    top_block("Top 30 Días", top_30_list, "#673AB7"),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START)
            ], scroll=ft.ScrollMode.AUTO),
            expand=True
        ),
        3: list_section("Historial ventas",   history_sales_list),
        4: list_section("Historial gastos",   history_expenses_list),
        5: list_section("Fiados y abonos",    history_fiados_list),
    }

    nav_labels = ["Métricas generales","Flujo de caja","Top productos",
                  "Historial ventas","Historial gastos","Fiados y abonos"]

    current_section = [0]
    content_area = ft.Container(content=sections_map[0], expand=True)
    nav_buttons  = []

    def set_section(index):
        current_section[0] = index
        content_area.content = sections_map[index]
        for i, btn in enumerate(nav_buttons):
            btn.style = (style_active if i == index else style_inactive)
        page.update()

    style_active = ft.ButtonStyle(
        bgcolor=SURFACE, color=TEXT,
        shape=ft.RoundedRectangleBorder(radius=6),
        side=ft.BorderSide(2, PRIMARY),
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        alignment=ft.Alignment(-1.0, 0.0)
    )
    style_inactive = ft.ButtonStyle(
        bgcolor="transparent", color=DIM,
        shape=ft.RoundedRectangleBorder(radius=6),
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        alignment=ft.Alignment(-1.0, 0.0)
    )

    for i, label in enumerate(nav_labels):
        btn = ft.TextButton(
            label,
            style=style_active if i == 0 else style_inactive,
            on_click=lambda e, idx=i: set_section(idx),
            width=float("inf"),
        )
        nav_buttons.append(btn)

    left_nav = ft.Container(
        content=ft.Column([
            ft.Text(f"Período: {today.strftime('%B %Y')}", size=12, color=DIM),
            ft.Container(height=12),
            *nav_buttons,
            ft.Container(expand=True),
            ft.OutlinedButton(
                "Exportar PDF",
                on_click=lambda e: export_pdf(),
                style=ft.ButtonStyle(
                    side=ft.BorderSide(1, "#2196F3"), color=PRIMARY,
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                width=float("inf")
            )
        ], spacing=4, expand=True),
        width=220, bgcolor=SURFACE, padding=16,
        border_radius=10, border=ft.border.all(1, BORDER)
    )

    filter_bar = ft.Row([
        ft.TextField(ref=start_date_ref, value=str(first_day),
                     bgcolor=SURFACE, filled=True, color=TEXT, height=42,
                     content_padding=10, border_color="#555555",
                     on_submit=refresh_report, keyboard_type=ft.KeyboardType.DATETIME, text_size=14),
        ft.TextField(ref=end_date_ref, value=str(today),
                     bgcolor=SURFACE, filled=True, color=TEXT, height=42,
                     content_padding=10, border_color="#555555",
                     on_submit=refresh_report, keyboard_type=ft.KeyboardType.DATETIME, text_size=14),
        ft.FilledButton("Filtrar", on_click=refresh_report,
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="white"), height=42)
    ], spacing=10)

    refresh_report()

    return ft.Container(
        content=ft.Column([
            filter_bar,
            ft.Container(height=12),
            ft.Row([
                left_nav,
                ft.Container(
                    content=content_area,
                    expand=True, bgcolor=SURFACE, padding=20,
                    border_radius=10, border=ft.border.all(1, BORDER)
                )
            ], spacing=12, expand=True, vertical_alignment=ft.CrossAxisAlignment.START)
        ], expand=True),
        padding=20, expand=True, bgcolor=BG
    )
