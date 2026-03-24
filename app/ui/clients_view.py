import flet as ft
from app.utils.helpers import show_message, is_mobile

def build_clients_view(page: ft.Page, model):
    # --- Estado Local ---
    clients_list = ft.ListView(spacing=0, expand=True, padding=0)
    search_field = ft.TextField(
        hint_text="Buscar cliente...",
        hint_style=ft.TextStyle(color="#666666"),
        bgcolor="#2c2c2c",
        filled=True,
        border_color="#444444",
        color="white",
        height=48,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=10),
        text_size=15,
        expand=True,
        on_change=lambda e: filter_clients(e.control.value)
    )

    # Stat labels
    txt_deuda_total = ft.Text("$0", size=22, weight="bold", color="#F44336")
    txt_clientes_activos = ft.Text("0", size=22, weight="bold", color="white")
    txt_mayor_deuda = ft.Text("—", size=16, weight="bold", color="white")

    all_clients = []

    # --- Dialogos ---
    dlg_new_client = ft.AlertDialog(title=ft.Text("Nuevo Cliente"))
    dlg_edit_client = ft.AlertDialog(title=ft.Text("Editar Cliente"))
    dlg_client_detail = ft.AlertDialog(title=ft.Text("Detalle Cliente"))
    dlg_payment = ft.AlertDialog(title=ft.Text("Registrar Pago"))
    dlg_confirm_delete = ft.AlertDialog(title=ft.Text("Confirmar Eliminación"))

    def close_dialog(dlg):
        dlg.open = False
        page.update()

    # --- Helpers ---
    def get_initials(name: str) -> str:
        parts = name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return name[:2].upper() if len(name) >= 2 else name.upper()

    def get_avatar_color(name: str) -> str:
        colors = ["#1976D2", "#388E3C", "#7B1FA2", "#F57C00", "#0097A7", "#C62828", "#00796B", "#5D4037"]
        return colors[sum(ord(c) for c in name) % len(colors)]

    # --- Acciones ---
    def open_new_client_dialog(e):
        name_field = ft.TextField(label="Nombre", autofocus=True)
        phone_field = ft.TextField(label="Teléfono", keyboard_type=ft.KeyboardType.PHONE)
        alias_field = ft.TextField(label="Alias (Opcional)")
        limit_field = ft.TextField(label="Límite de Crédito (Opcional)", value="0", keyboard_type=ft.KeyboardType.NUMBER)

        def save_client(e):
            nombre = name_field.value.strip()
            if not nombre:
                show_message(page, "El nombre es obligatorio", "orange")
                return
            try:
                limite = float(limit_field.value) if limit_field.value else 0
                model.add_client(nombre, phone_field.value, alias_field.value, limite)
                close_dialog(dlg_new_client)
                show_message(page, f"Cliente '{nombre}' creado", "green")
                refresh_clients()
            except ValueError:
                show_message(page, "El límite debe ser un número", "red")
            except Exception as ex:
                show_message(page, f"Error: {ex}", "red")

        dlg_new_client.content = ft.Column([name_field, phone_field, alias_field, limit_field], tight=True, width=300)
        dlg_new_client.actions = [
            ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_new_client)),
            ft.FilledButton("Guardar", on_click=save_client, style=ft.ButtonStyle(bgcolor="blue", color="white"))
        ]
        if dlg_new_client not in page.overlay:
            page.overlay.append(dlg_new_client)
        dlg_new_client.open = True
        page.update()

    def open_edit_client_dialog(client):
        name_field = ft.TextField(label="Nombre", value=client['nombre'], autofocus=True)
        phone_field = ft.TextField(label="Teléfono", value=client['telefono'], keyboard_type=ft.KeyboardType.PHONE)
        alias_field = ft.TextField(label="Alias", value=client['alias'])
        limit_field = ft.TextField(label="Límite de Crédito", value=str(int(client['limite'])), keyboard_type=ft.KeyboardType.NUMBER)

        def update_client_action(e):
            nombre = name_field.value.strip()
            if not nombre:
                show_message(page, "El nombre es obligatorio", "orange")
                return
            try:
                limite = float(limit_field.value) if limit_field.value else 0
                model.update_client(client['id'], nombre, phone_field.value, alias_field.value, limite)
                close_dialog(dlg_edit_client)
                show_message(page, "Cliente actualizado", "green")
                refresh_clients()
            except ValueError:
                show_message(page, "Límite inválido", "red")
            except Exception as ex:
                show_message(page, f"Error: {ex}", "red")

        dlg_edit_client.content = ft.Column([name_field, phone_field, alias_field, limit_field], tight=True, width=300)
        dlg_edit_client.actions = [
            ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_edit_client)),
            ft.FilledButton("Actualizar", on_click=update_client_action, style=ft.ButtonStyle(bgcolor="blue", color="white"))
        ]
        if dlg_edit_client not in page.overlay:
            page.overlay.append(dlg_edit_client)
        dlg_edit_client.open = True
        page.update()

    def delete_client_click(client):
        def confirm_delete(e):
            try:
                model.delete_client(client['id'])
                close_dialog(dlg_confirm_delete)
                show_message(page, "Cliente eliminado", "green")
                refresh_clients()
            except Exception as ex:
                show_message(page, f"Error: {ex}", "red")

        dlg_confirm_delete.content = ft.Text(f"¿Eliminar a '{client['nombre']}'? Se borrará todo su historial.", size=16)
        dlg_confirm_delete.actions = [
            ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_confirm_delete)),
            ft.FilledButton("Eliminar", on_click=confirm_delete, style=ft.ButtonStyle(bgcolor="red", color="white"))
        ]
        if dlg_confirm_delete not in page.overlay:
            page.overlay.append(dlg_confirm_delete)
        dlg_confirm_delete.open = True
        page.update()

    def open_client_detail(client):
        movements = model.get_client_movements(client['id'])
        history_items = []
        for mov in movements:
            m_date = mov[2][2:10]
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

        def open_payment_dialog(e):
            amount_field = ft.TextField(label="Monto a Pagar", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
            payment_method_dropdown = ft.Dropdown(
                label="Método de Pago",
                options=[
                    ft.dropdown.Option("EFECTIVO", "💵 Efectivo"),
                    ft.dropdown.Option("DEBITO", "💳 Débito"),
                    ft.dropdown.Option("CREDITO", "💳 Crédito"),
                    ft.dropdown.Option("TRANSFERENCIA", "📱 Transferencia"),
                ],
                value="EFECTIVO",
                width=200
            )
            def save_payment(e):
                try:
                    monto = float(amount_field.value)
                    if monto <= 0: return
                    medio_pago = payment_method_dropdown.value
                    model.add_movement(client['id'], 'PAGO', monto, "Abono / Pago", medio_pago=medio_pago)
                    close_dialog(dlg_payment)
                    close_dialog(dlg_client_detail)
                    show_message(page, f"Pago de ${monto:,.0f} registrado ({medio_pago})", "green")
                    refresh_clients()
                except ValueError:
                    show_message(page, "Monto inválido", "red")
            dlg_payment.content = ft.Column([amount_field, payment_method_dropdown], tight=True, spacing=10)
            dlg_payment.actions = [
                ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_payment)),
                ft.FilledButton("Confirmar", on_click=save_payment, style=ft.ButtonStyle(bgcolor="green", color="white"))
            ]
            if dlg_payment not in page.overlay:
                page.overlay.append(dlg_payment)
            dlg_payment.open = True
            page.update()

        dlg_content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.FilledButton("Registrar Pago", icon="attach_money",
                                    style=ft.ButtonStyle(bgcolor="green", color="white"),
                                    on_click=open_payment_dialog),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(color="white24"),
                ft.Text("Historial de Movimientos", weight="bold", color="white"),
                ft.Container(content=ft.ListView(controls=history_items, expand=True, spacing=0, padding=0), height=300),
            ], width=600, height=400),
            bgcolor="#212121",
            padding=20,
            border_radius=10
        )
        dlg_client_detail.title = ft.Text(f"{client['nombre']} - Saldo: ${client['saldo_actual']:,.0f}", color="white")
        dlg_client_detail.content = dlg_content
        dlg_client_detail.bgcolor = "#212121"
        dlg_client_detail.actions = [ft.TextButton("Cerrar", on_click=lambda e: close_dialog(dlg_client_detail))]
        if dlg_client_detail not in page.overlay:
            page.overlay.append(dlg_client_detail)
        dlg_client_detail.open = True
        page.update()

    def open_quick_payment(client):
        amount_field = ft.TextField(label="Monto a Abonar", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
        payment_method_dropdown = ft.Dropdown(
            label="Método de Pago",
            options=[
                ft.dropdown.Option("EFECTIVO", "💵 Efectivo"),
                ft.dropdown.Option("DEBITO", "💳 Débito"),
                ft.dropdown.Option("CREDITO", "💳 Crédito"),
                ft.dropdown.Option("TRANSFERENCIA", "📱 Transferencia"),
            ],
            value="EFECTIVO",
            width=200
        )
        def save_payment(e):
            try:
                monto = float(amount_field.value)
                if monto <= 0: return
                medio_pago = payment_method_dropdown.value
                model.add_movement(client['id'], 'PAGO', monto, "Abono / Pago", medio_pago=medio_pago)
                close_dialog(dlg_payment)
                show_message(page, f"Abono de ${monto:,.0f} registrado", "green")
                refresh_clients()
            except ValueError:
                show_message(page, "Monto inválido", "red")
        dlg_payment.title = ft.Text(f"Abonar - {client['nombre']}")
        dlg_payment.content = ft.Column([amount_field, payment_method_dropdown], tight=True, spacing=10)
        dlg_payment.actions = [
            ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_payment)),
            ft.FilledButton("Confirmar", on_click=save_payment, style=ft.ButtonStyle(bgcolor="green", color="white"))
        ]
        if dlg_payment not in page.overlay:
            page.overlay.append(dlg_payment)
        dlg_payment.open = True
        page.update()

    def build_client_row(c):
        has_debt = c['saldo_actual'] > 0
        debt_color = "#F44336" if has_debt else "#4CAF50"
        debt_label = f"${c['saldo_actual']:,.0f}" if has_debt else "$0"
        debt_sublabel = "deuda" if has_debt else "al día"

        # Avatar de iniciales
        initials = get_initials(c['nombre'])
        av_color = get_avatar_color(c['nombre'])
        avatar = ft.Container(
            content=ft.Text(initials, color="white", weight="bold", size=14),
            bgcolor=av_color,
            width=44, height=44,
            border_radius=22,
            alignment=ft.alignment.center
        )

        # Progreso de crédito
        limite = c['limite']
        saldo = c['saldo_actual']
        progress_controls = []
        if limite > 0:
            ratio = min(saldo / limite, 1.0)
            pct = int(ratio * 100)
            progress_controls = [
                ft.ProgressBar(value=ratio, color="#F44336", bgcolor="#3a3a3a", height=4, border_radius=2, width=float("inf")),
                ft.Text(f"Límite ${limite:,.0f} · {pct}% usado", size=11, color="#888888")
            ]
        else:
            progress_controls = [
                ft.Text("Sin límite", size=11, color="#888888")
            ]

        alias_str = f"· {c['alias']}" if c['alias'] else "· Sin alias"

        return ft.Container(
            content=ft.Row([
                avatar,
                ft.Column([
                    ft.Text(f"{c['nombre']} {alias_str}", size=15, weight="bold", color="white",
                            overflow=ft.TextOverflow.ELLIPSIS),
                    *progress_controls
                ], expand=True, spacing=4),
                ft.Column([
                    ft.Text(debt_label, size=16, weight="bold", color=debt_color),
                    ft.Text(debt_sublabel, size=11, color="#888888")
                ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
                ft.Column([
                    ft.OutlinedButton(
                        "Historial",
                        style=ft.ButtonStyle(
                            side=ft.BorderSide(1, "#555555"),
                            color="white",
                            shape=ft.RoundedRectangleBorder(radius=6),
                            padding=ft.padding.symmetric(horizontal=10, vertical=4)
                        ),
                        height=32,
                        on_click=lambda e, cl=c: open_client_detail(cl)
                    ),
                    ft.OutlinedButton(
                        "Abono",
                        style=ft.ButtonStyle(
                            side=ft.BorderSide(1, "#4CAF50"),
                            color="#4CAF50",
                            shape=ft.RoundedRectangleBorder(radius=6),
                            padding=ft.padding.symmetric(horizontal=10, vertical=4)
                        ),
                        height=32,
                        on_click=lambda e, cl=c: open_quick_payment(cl)
                    ) if has_debt else ft.Container(width=80, height=32),
                ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.END),
            ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=20, vertical=14),
            border=ft.border.only(bottom=ft.border.BorderSide(1, "#2a2a2a")),
            bgcolor="#1e1e1e",
            on_click=lambda e, cl=c: open_client_detail(cl),
            ink=False
        )

    def render_clients(clients):
        clients_list.controls.clear()
        if not clients:
            clients_list.controls.append(
                ft.Container(
                    ft.Text("No se encontraron clientes", color="#888888", text_align="center"),
                    padding=30, alignment=ft.alignment.center
                )
            )
        else:
            for c in clients:
                clients_list.controls.append(build_client_row(c))
        page.update()

    def filter_clients(query: str):
        if not query:
            render_clients(all_clients)
        else:
            q = query.lower()
            filtered = [c for c in all_clients if q in c['nombre'].lower() or (c['alias'] and q in c['alias'].lower())]
            render_clients(filtered)

    def refresh_clients():
        nonlocal all_clients
        all_clients = model.get_clients_with_balance()

        # Stats
        with_debt = [c for c in all_clients if c['saldo_actual'] > 0]
        total_deuda = sum(c['saldo_actual'] for c in with_debt)
        txt_deuda_total.value = f"${total_deuda:,.0f}"
        txt_clientes_activos.value = str(len(with_debt))
        if with_debt:
            mayor = max(with_debt, key=lambda c: c['saldo_actual'])
            txt_mayor_deuda.value = mayor['nombre']
        else:
            txt_mayor_deuda.value = "—"

        render_clients(all_clients)

    # --- Layout Principal ---
    stat_cards = ft.Row([
        ft.Container(
            content=ft.Column([
                ft.Text("Deuda total", color="#aaaaaa", size=12),
                txt_deuda_total
            ], spacing=2),
            bgcolor="#2c2c2c", padding=16, border_radius=10, expand=True
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Clientes activos", color="#aaaaaa", size=12),
                txt_clientes_activos
            ], spacing=2),
            bgcolor="#2c2c2c", padding=16, border_radius=10, expand=True
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Mayor deuda", color="#aaaaaa", size=12),
                txt_mayor_deuda
            ], spacing=2),
            bgcolor="#2c2c2c", padding=16, border_radius=10, expand=True
        ),
    ], spacing=10)

    refresh_clients()

    return ft.Container(
        content=ft.Column([
            # Barra busqueda + boton
            ft.Row([
                search_field,
                ft.FilledButton(
                    "+ Nuevo cliente",
                    on_click=open_new_client_dialog,
                    style=ft.ButtonStyle(bgcolor="#1976D2", color="white"),
                    height=48
                )
            ], spacing=10),
            ft.Container(height=10),
            stat_cards,
            ft.Container(height=10),
            # Lista de clientes
            ft.Container(
                content=clients_list,
                expand=True,
                bgcolor="#1e1e1e",
                border_radius=10,
                border=ft.border.all(1, "#2a2a2a"),
                clip_behavior=ft.ClipBehavior.HARD_EDGE
            )
        ], expand=True, spacing=0),
        padding=20,
        expand=True,
        bgcolor="#121212"
    )
