import flet as ft
from app.utils.helpers import show_message, is_mobile

def build_clients_view(page: ft.Page, model):
    # --- Estado Local ---
    clients_grid = ft.GridView(
        expand=True,
        runs_count=5,
        max_extent=300,
        child_aspect_ratio=1.0,
        spacing=10,
        run_spacing=10,
    )
    
    # --- Dialogos ---
    dlg_new_client = ft.AlertDialog(title=ft.Text("Nuevo Cliente"))
    dlg_client_detail = ft.AlertDialog(title=ft.Text("Detalle Cliente"))
    dlg_payment = ft.AlertDialog(title=ft.Text("Registrar Pago"))
    dlg_debt = ft.AlertDialog(title=ft.Text("Agregar Deuda Manual"))

    def close_dialog(dlg):
        dlg.open = False
        page.update()

    # --- Acciones ---
    
    def open_new_client_dialog(e):
        name_field = ft.TextField(label="Nombre", autofocus=True)
        phone_field = ft.TextField(label="Teléfono", keyboard_type=ft.KeyboardType.PHONE)
        alias_field = ft.TextField(label="Alias (Opcional)")
        
        def save_client(e):
            nombre = name_field.value.strip()
            if not nombre:
                show_message(page, "El nombre es obligatorio", "orange")
                return
            
            try:
                model.add_client(nombre, phone_field.value, alias_field.value)
                close_dialog(dlg_new_client)
                show_message(page, f"Cliente '{nombre}' creado", "green")
                refresh_clients()
            except Exception as ex:
                show_message(page, f"Error: {ex}", "red")

        dlg_new_client.content = ft.Column([name_field, phone_field, alias_field], tight=True, width=300)
        dlg_new_client.actions = [
            ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_new_client)),
            ft.ElevatedButton("Guardar", on_click=save_client, bgcolor="blue", color="white")
        ]
        if dlg_new_client not in page.overlay:
            page.overlay.append(dlg_new_client)
        dlg_new_client.open = True
        page.update()

    def open_client_detail(client):
        # Cargar historial
        movements = model.get_client_movements(client['id'])
        
        # Tabla de Movimientos
        history_rows = []
        for mov in movements:
            # mov: id, client_id, date, type, amount, desc, sale_id
            m_date = mov[2][:10] # Solo fecha
            m_type = mov[3]
            m_amount = mov[4]
            m_desc = mov[5]
            
            color = "red" if m_type == 'DEUDA' else "green"
            sign = "-" if m_type == 'DEUDA' else "+"
            
            history_rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(m_date, size=13, color="white")),
                    ft.DataCell(ft.Text(m_desc, size=13, color="white", width=150, no_wrap=False)),
                    ft.DataCell(ft.Text(m_type, color=color, weight="bold", size=13)),
                    ft.DataCell(ft.Text(f"{sign}${m_amount:,.0f}", color=color, weight="bold", size=13)),
                ])
            )

        history_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Fecha", color="black", weight="bold")),
                ft.DataColumn(ft.Text("Descripción", color="black", weight="bold")),
                ft.DataColumn(ft.Text("Tipo", color="black", weight="bold")),
                ft.DataColumn(ft.Text("Monto", color="black", weight="bold")),
            ],
            rows=history_rows,
            border=ft.border.all(1, "#eeeeee"),
            vertical_lines=ft.border.all(1, "#eeeeee"),
            heading_row_color="#f0f0f0",
        )

        def open_payment_dialog(e):
            amount_field = ft.TextField(label="Monto a Pagar", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
            
            def save_payment(e):
                try:
                    monto = float(amount_field.value)
                    if monto <= 0: return
                    
                    model.add_movement(client['id'], 'PAGO', monto, "Abono / Pago")
                    close_dialog(dlg_payment)
                    close_dialog(dlg_client_detail) # Cerrar detalle para refrescar
                    show_message(page, f"Pago de ${monto:,.0f} registrado", "green")
                    refresh_clients()
                except ValueError:
                    show_message(page, "Monto inválido", "red")

            dlg_payment.content = amount_field
            dlg_payment.actions = [
                ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_payment)),
                ft.ElevatedButton("Confirmar Pago", on_click=save_payment, bgcolor="green", color="white")
            ]
            if dlg_payment not in page.overlay:
                page.overlay.append(dlg_payment)
            dlg_payment.open = True
            page.update()
        
        # Botones de Acción
        actions_row = ft.Row([
            ft.ElevatedButton("Registrar Pago", icon="attach_money", bgcolor="green", color="white", on_click=open_payment_dialog),
            # ft.OutlinedButton("Agregar Deuda Manual", icon="remove_circle", on_click=None) # Opcional
        ], alignment=ft.MainAxisAlignment.CENTER)

        dlg_client_detail.title = ft.Text(f"{client['nombre']} - Saldo: ${client['saldo_actual']:,.0f}")
        dlg_client_detail.content = ft.Column([
            actions_row,
            ft.Divider(),
            ft.Text("Historial de Movimientos", weight="bold"),
            ft.Column([history_table], scroll=ft.ScrollMode.AUTO, height=300),
        ], width=600, height=400)
        
        dlg_client_detail.actions = [ft.TextButton("Cerrar", on_click=lambda e: close_dialog(dlg_client_detail))]
        
        if dlg_client_detail not in page.overlay:
            page.overlay.append(dlg_client_detail)
        dlg_client_detail.open = True
        page.update()

    def refresh_clients():
        clients_grid.controls.clear()
        clients = model.get_clients_with_balance()
        
        for c in clients:
            status_color = "green" if c['saldo_actual'] <= 0 else "red"
            status_text = "AL DÍA" if c['saldo_actual'] <= 0 else f"DEUDA: ${c['saldo_actual']:,.0f}"
            
            # Diseño de Tarjeta mejorado
            card_content = ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, size=30, color="#42A5F5"), # Lighter Blue
                    ft.Column([
                        ft.Text(c['nombre'], weight="bold", size=16, color="white"),
                        ft.Text(c['alias'] if c['alias'] else "Sin Alias", size=12, color="white70"),
                    ], spacing=2, expand=True),
                ], alignment="start"),
                
                ft.Divider(height=10, color="transparent"),
                
                ft.Container(
                    content=ft.Row([
                        ft.Text("Estado:", size=12, color="white70"),
                        ft.Text(status_text, color=status_color, weight="bold", size=14)
                    ], alignment="spaceBetween"),
                    padding=5,
                    border=ft.border.all(1, "#424242"), # Darker Grey Border
                    border_radius=8
                ),
                
                ft.Container(expand=True), # Spacer
                
                ft.ElevatedButton(
                    "Ver Historial",
                    icon="visibility",
                    style=ft.ButtonStyle(
                        color="white",
                        bgcolor="#1976D2",
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda e, cl=c: open_client_detail(cl),
                    height=35,
                    width=None,
                )
            ], spacing=5)

            card = ft.Card(
                content=ft.Container(
                    content=card_content,
                    padding=15,
                    width=250, # Ancho fijo para consistencia
                    height=200, # Alto fijo
                ),
                elevation=2,
                color="#212121", # Fondo oscuro para contraste
            )
            clients_grid.controls.append(card)
        
        page.update()

    # --- Layout Principal ---
    # Header Responsivo
    title_text = ft.Text("El Cuaderno Digital", size=24, weight="bold", color="#1976D2")
    new_btn = ft.ElevatedButton("Nuevo Cliente", icon="add", on_click=open_new_client_dialog, bgcolor="#1976D2", color="white")
    
    if is_mobile(page):
        header = ft.Column([
            title_text,
            new_btn
        ], spacing=10, alignment=ft.MainAxisAlignment.START)
    else:
        header = ft.Row([
            title_text,
            new_btn
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # Initial Load
    refresh_clients()

    return ft.Container(
        content=ft.Column([
            header,
            ft.Divider(),
            clients_grid
        ], expand=True),
        padding=20,
        expand=True
    )
