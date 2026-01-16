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
        
        # Lista de Movimientos (Mobile Friendly)
        history_items = []
        for mov in movements:
            # mov[2] es "YYYY-MM-DD HH:MM:SS" -> tomamos "YY-MM-DD"
            m_date = mov[2][2:10] # 2026-01-15 -> 26-01-15
            m_type = mov[3]
            m_amount = mov[4]
            m_desc = mov[5]
            
            is_debt = m_type == 'DEUDA'
            color = "red" if is_debt else "green"
            icon = ft.Icons.REMOVE_CIRCLE_OUTLINE if is_debt else ft.Icons.ADD_CIRCLE_OUTLINE
            sign = "-" if is_debt else "+"
            
            history_items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(icon, color=color, size=20),
                        ft.Column([
                            ft.Text(m_desc, color="white", weight="bold", size=14, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"{m_date} • {m_type}", color="white54", size=12),
                        ], expand=True, spacing=2),
                        ft.Text(f"{sign}${m_amount:,.0f}", color=color, weight="bold", size=14),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10,
                    border=ft.border.only(bottom=ft.border.BorderSide(1, "#333333")),
                )
            )

        history_list = ft.ListView(
            controls=history_items,
            expand=True,
            spacing=0,
            padding=0,
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
                ft.ElevatedButton("Confirmar", on_click=save_payment, bgcolor="green", color="white")
            ]
            dlg_payment.actions_alignment = ft.MainAxisAlignment.SPACE_BETWEEN # Alinear extremos
            
            if dlg_payment not in page.overlay:
                page.overlay.append(dlg_payment)
            dlg_payment.open = True
            page.update()
        
        # Botones de Acción
        actions_row = ft.Row([
            ft.ElevatedButton("Registrar Pago", icon="attach_money", bgcolor="green", color="white", on_click=open_payment_dialog),
        ], alignment=ft.MainAxisAlignment.CENTER)

        # Dialogo con Tema Oscuro
        dlg_content = ft.Container(
            content=ft.Column([
                actions_row,
                ft.Divider(color="white24"),
                ft.Text("Historial de Movimientos", weight="bold", color="white"),
                ft.Container(content=history_list, height=300, padding=0),
            ], width=600, height=400),
            bgcolor="#212121",
            padding=20,
            border_radius=10
        )
        
        dlg_client_detail.title = ft.Text(f"{client['nombre']} - Saldo: ${client['saldo_actual']:,.0f}", color="white")
        dlg_client_detail.content = dlg_content
        dlg_client_detail.bgcolor = "#212121" # Fondo del cuadro de diálogo
        
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
                    height=30, # Un poco más compacto
                    width=None,
                )
            ], spacing=5)

            card = ft.Card(
                content=ft.Container(
                    content=card_content,
                    padding=10, # Reducir padding
                    width=250, 
                    height=165, # Reducir altura de 200 -> 165
                    bgcolor="#212121", 
                    border_radius=12, 
                ),
                elevation=2,
            )
            clients_grid.controls.append(card)
        
        page.update()

    # --- Layout Principal ---
    # Header Responsivo
    # Header Responsivo con Grilla
    header = ft.ResponsiveRow([
        ft.Container(
            content=ft.Text("El Cuaderno Digital", size=24, weight="bold", color="#1976D2"),
            col={"xs": 12, "md": 8},
            alignment=ft.Alignment(-1, 0), # Center Left
        ),
        ft.Container(
            content=ft.ElevatedButton("Nuevo Cliente", icon="add", on_click=open_new_client_dialog, bgcolor="#1976D2", color="white", width=500), 
            col={"xs": 12, "md": 4},
            alignment=ft.Alignment(-1, 0) if is_mobile(page) else ft.Alignment(1, 0), # Center Left (Mobile) / Center Right (Desktop)
        )
    ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

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
