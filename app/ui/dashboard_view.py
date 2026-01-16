import flet as ft
from app.utils.helpers import is_mobile, show_message


def build_dashboard_view(page: ft.Page, model, on_logout_callback=None):
    # ==========================
    # 1. ESTADO Y CALCULOS
    # ==========================
    
    # Textos de resumen
    txt_total_ventas = ft.Text("$0", size=24, weight="bold", color="white")
    txt_total_gastos = ft.Text("$0", size=24, weight="bold", color="white")
    txt_ganancia = ft.Text("$0", size=24, weight="bold", color="white")
    
    # Listas
    sales_list = ft.ListView(spacing=5, height=200, padding=10)
    expenses_list = ft.ListView(spacing=5, height=200, padding=10)
    
    def refresh_data():
        sales = model.get_sales_report()
        expenses = model.get_expenses_report()
        
        # Calcular totales
        total_s = sum(row[2] for row in sales) if sales else 0
        total_e = sum(row[2] for row in expenses) if expenses else 0
        profit = total_s - total_e
        
        # Actualizar tarjetas
        txt_total_ventas.value = f"${total_s:,.0f}"
        txt_total_gastos.value = f"${total_e:,.0f}"
        txt_ganancia.value = f"${profit:,.0f}"
        
        # Color dinámico para ganancia
        if profit >= 0:
            card_profit.bgcolor = "#4CAF50" # Verde
            txt_ganancia.color = "white"
        else:
            card_profit.bgcolor = "#F44336" # Rojo
            txt_ganancia.color = "white"
            
        # Llenar lista de ventas (Ultimas 10)
        sales_list.controls.clear()
        if not sales:
            sales_list.controls.append(ft.Text("No hay ventas registradas", color="grey"))
        else:
            for s in sales[:10]: # Solo las 10 ultimas
                sid, fecha, total = s
                # Formatear fecha simple (cortando segundos si es ISO)
                fecha_fmt = fecha.split('T')[0] 
                sales_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(f"#{sid} - {fecha_fmt}", size=12),
                            ft.Text(f"${total:,.0f}", weight="bold", color="green"),
                        ], alignment="space_between"),
                        bgcolor="white", padding=5, border_radius=5
                    )
                )
                
        # Llenar lista de gastos
        expenses_list.controls.clear()
        if not expenses:
            expenses_list.controls.append(ft.Text("No hay gastos registrados", color="grey"))
        else:
            for e in expenses[:10]:
                eid, desc, monto, fecha, cat = e
                fecha_fmt = fecha.split('T')[0]
                expenses_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(f"{desc} ({fecha_fmt})", size=12),
                            ft.Text(f"-${monto:,.0f}", weight="bold", color="red"),
                        ], alignment="space_between"),
                        bgcolor="white", padding=5, border_radius=5
                    )
                )
        
        page.update()

    # ==========================
    # 2. UI - TARJETAS SUPERIORES
    # ==========================
    def build_stat_card(title, value_control, color):
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    title, 
                    color="white", 
                    size=14, 
                    weight="w500",
                    text_align="center"
                ),
                ft.Container(height=5),  # Espaciado
                value_control
            ], 
            alignment=ft.MainAxisAlignment.CENTER, 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0),
            bgcolor=color,
            padding=ft.padding.symmetric(vertical=25, horizontal=20),
            border_radius=12,
            expand=True,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.2, "black"),
                offset=ft.Offset(0, 2),
            )
        )

    card_sales = build_stat_card("VENTAS", txt_total_ventas, "#2196F3")
    card_expenses = build_stat_card("GASTOS", txt_total_gastos, "#FF9800")
    card_profit = build_stat_card("GANANCIA", txt_ganancia, "#4CAF50")  # Bgcolor se actualiza dinamicamente

    # ==========================
    # 3. FORMULARIO DE GASTOS
    # ==========================
    desc_field = ft.TextField(label="Descripción del Gasto", hint_text="Ej: Luz, Internet", bgcolor="white", filled=True)
    amount_field = ft.TextField(label="Monto", hint_text="5000", keyboard_type=ft.KeyboardType.NUMBER, bgcolor="white", filled=True)
    
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
            show_message(page, "Gasto registrado correctamente", "green")
        except ValueError:
            show_message(page, "Monto inválido", "red")
        except Exception as ex:
            show_message(page, f"Error: {str(ex)}", "red")

    expense_form = ft.Container(
        content=ft.Column([
            ft.Text("REGISTRAR GASTO", weight="bold", size=16, color="#D32F2F"),
            ft.Container(height=10),  # Espaciado
            ft.ResponsiveRow([
                ft.Column([desc_field], col={"xs": 10, "sm": 10, "md": 8}),
                ft.Column([amount_field], col={"xs": 10, "sm": 10, "md": 4}),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.ElevatedButton(
                "Registrar Gasto", 
                on_click=add_expense_click, 
                bgcolor="#F44336", 
                color="white",
                width=200,
            )
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor="white",
        padding=20,
        border_radius=10,
        border=ft.border.all(1, "#E0E0E0"),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=4,
            color=ft.Colors.with_opacity(0.1, "black"),
            offset=ft.Offset(0, 2),
        )
    )

    refresh_data() # Cargar datos iniciales
    
    return ft.Container(
        content=ft.ListView([
            # Cabecera con Titulo
            ft.Container(
                content=ft.Row([
                    ft.Text("PANEL FINANCIERO", size=24, weight="bold", color="white"),
                ], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor="#607D8B", padding=15, border_radius=10
            ),
            # Tarjetas
            ft.ResponsiveRow([
                ft.Column([card_sales], col={"xs": 12, "md": 4}),
                ft.Column([card_expenses], col={"xs": 12, "md": 4}),
                ft.Column([card_profit], col={"xs": 12, "md": 4}),
            ], spacing=10),
            # Form Gasto
            expense_form,
            # Listas
            ft.ResponsiveRow([
                ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Historial de Ventas", weight="bold", size=16, color="#2E7D32"), 
                            sales_list
                        ]),
                        bgcolor="#E8F5E9", padding=10, border_radius=10
                    )
                ], col={"xs": 12, "md": 6}),
                ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Historial de Gastos", weight="bold", size=16, color="#C62828"), 
                            expenses_list
                        ]),
                        bgcolor="#FFEBEE", padding=10, border_radius=10
                    )
                ], col={"xs": 12, "md": 6}),
            ]),
        ], spacing=15, padding=10),
        expand=True
    )
