"""
pdf_exporter.py — Generador de reporte PDF para Digital PyME
Requiere: reportlab  (pip install reportlab)
"""
import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Paleta ──────────────────────────────────────────────────────────────────
DARK   = colors.HexColor("#1e1e1e")
ACCENT = colors.HexColor("#2196F3")
GREEN  = colors.HexColor("#4CAF50")
RED    = colors.HexColor("#F44336")
ORANGE = colors.HexColor("#FF9800")
GRAY   = colors.HexColor("#888888")
LIGHT  = colors.HexColor("#f5f5f5")
WHITE  = colors.white
BLACK  = colors.black

W, H = A4  # 21 x 29.7 cm

def generate_report_pdf(report_data: dict, output_path: str) -> str:
    """
    Genera el PDF con los datos del reporte y lo guarda en output_path.
    Retorna la ruta del archivo generado.

    report_data keys esperados:
      - start_date, end_date (str)
      - total_ventas, total_gastos, utilidad (float)
      - flujo_entradas, total_fiado, total_abonos (float)
      - tx_count, exp_count (int)
      - top_products: list[tuple(name, qty)]
      - sales_history: list[tuple(id, fecha, total, pago)]
      - expenses_history: list[tuple(id, desc, monto, fecha)]
      - clients_debt: list[dict{nombre, alias, saldo_actual}]
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )

    styles = getSampleStyleSheet()
    story  = []

    def S(name, **kw):
        return ParagraphStyle(name, parent=styles["Normal"], **kw)

    title_style   = S("T", fontSize=20, textColor=BLACK, spaceAfter=2, leading=24)
    sub_style     = S("Sub", fontSize=11, textColor=GRAY, spaceAfter=6)
    section_style = S("Sec", fontSize=13, textColor=DARK, fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=4)
    body_style    = S("Body", fontSize=10, textColor=BLACK)
    right_style   = S("R", fontSize=10, textColor=BLACK, alignment=TA_RIGHT)
    note_style    = S("Note", fontSize=8, textColor=GRAY, italic=True, spaceBefore=8)

    # ── Encabezado ───────────────────────────────────────────────────────────
    story.append(Paragraph("Digital PyME — Reporte Financiero", title_style))
    story.append(Paragraph(
        f"Período: {report_data.get('start_date','')}  →  {report_data.get('end_date','')}   |   "
        f"Generado el {datetime.date.today().strftime('%d/%m/%Y')}",
        sub_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=DARK, spaceAfter=8))

    # ── Métricas principales ─────────────────────────────────────────────────
    story.append(Paragraph("Métricas generales", section_style))

    ventas  = report_data.get("total_ventas", 0)
    gastos  = report_data.get("total_gastos", 0)
    util    = report_data.get("utilidad", 0)
    entradas= report_data.get("flujo_entradas", 0)
    fiado   = report_data.get("total_fiado", 0)
    abonos  = report_data.get("total_abonos", 0)
    tx      = report_data.get("tx_count", 0)
    pct     = (util / ventas * 100) if ventas > 0 else 0

    m_data = [
        ["", "Concepto", "Monto"],
        ["💰", "Ventas brutas",      f"${ventas:,.0f}"],
        ["📉", "Gastos operativos",  f"${gastos:,.0f}"],
        ["✅", "Utilidad aprox.",    f"${util:,.0f}  ({pct:.1f}%)"],
        ["🏦", "Efectivo en caja",   f"${entradas:,.0f}"],
        ["📘", "Vendido al fiado",   f"${fiado:,.0f}"],
        ["🔄", "Abonos recibidos",   f"${abonos:,.0f}"],
    ]
    m_style = TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), ACCENT),
        ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [LIGHT, WHITE]),
        ("GRID",        (0,0), (-1,-1), 0.3, GRAY),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING",(0,0), (-1,-1), 8),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        # Color utilidad
        ("TEXTCOLOR",   (2,3), (2,3), GREEN if util >= 0 else RED),
        ("TEXTCOLOR",   (2,6), (2,6), GREEN),
        ("TEXTCOLOR",   (2,5), (2,5), ORANGE),
    ])
    m_table = Table(m_data, colWidths=[1*cm, 9*cm, 5.5*cm])
    m_table.setStyle(m_style)
    story.append(m_table)
    story.append(Paragraph(f"Total transacciones: {tx}", note_style))
    story.append(Spacer(1, 0.4*cm))

    # ── Top productos ────────────────────────────────────────────────────────
    tops = report_data.get("top_products", [])
    if tops:
        story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceAfter=4))
        story.append(Paragraph("Top productos (últimos 30 días)", section_style))
        tp_data = [["#", "Producto", "Unidades vendidas"]]
        for i, (name, qty) in enumerate(tops, 1):
            tp_data.append([str(i), name, str(qty)])
        tp_style = TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), DARK),
            ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 10),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [LIGHT, WHITE]),
            ("GRID",        (0,0), (-1,-1), 0.3, GRAY),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING",  (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ("ALIGN",       (2,0), (2,-1), "CENTER"),
            ("TEXTCOLOR",   (2,1), (2,-1), GREEN),
            ("FONTNAME",    (2,1), (2,-1), "Helvetica-Bold"),
        ])
        tp_table = Table(tp_data, colWidths=[1*cm, 10*cm, 4.5*cm])
        tp_table.setStyle(tp_style)
        story.append(tp_table)
        story.append(Spacer(1, 0.4*cm))

    # ── Historial de ventas ──────────────────────────────────────────────────
    sales = report_data.get("sales_history", [])
    if sales:
        story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceAfter=4))
        story.append(Paragraph(f"Historial de ventas ({len(sales)} registros)", section_style))
        sv_data = [["#Venta", "Fecha", "Total", "Método"]]
        for s in sales:
            s_id, s_fecha, s_total, s_pago = s[0], s[1], s[2], (s[3] if len(s) >= 4 else "EFECTIVO")
            dp = s_fecha.split("T")[0] if "T" in s_fecha else s_fecha
            tp_str = s_fecha.split("T")[1][:5] if "T" in s_fecha else ""
            sv_data.append([f"#{s_id}", f"{dp} {tp_str}", f"${s_total:,.0f}", s_pago or "EFECTIVO"])
        sv_style = TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), DARK),
            ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [LIGHT, WHITE]),
            ("GRID",        (0,0), (-1,-1), 0.3, GRAY),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING",  (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ("ALIGN",       (2,0), (2,-1), "RIGHT"),
            ("TEXTCOLOR",   (2,1), (2,-1), GREEN),
        ])
        sv_table = Table(sv_data, colWidths=[2*cm, 4.5*cm, 4*cm, 5*cm])
        sv_table.setStyle(sv_style)
        story.append(sv_table)
        story.append(Spacer(1, 0.4*cm))

    # ── Fiados pendientes ────────────────────────────────────────────────────
    fiados = report_data.get("clients_debt", [])
    if fiados:
        story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceAfter=4))
        story.append(Paragraph(f"Fiados pendientes ({len(fiados)} clientes)", section_style))
        fd_data = [["Cliente", "Alias", "Deuda"]]
        for c in fiados:
            fd_data.append([c.get("nombre",""), c.get("alias","") or "—", f"${c.get('saldo_actual',0):,.0f}"])
        fd_style = TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), RED),
            ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 10),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [LIGHT, WHITE]),
            ("GRID",        (0,0), (-1,-1), 0.3, GRAY),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING",  (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ("ALIGN",       (2,0), (2,-1), "RIGHT"),
            ("TEXTCOLOR",   (2,1), (2,-1), RED),
            ("FONTNAME",    (2,1), (2,-1), "Helvetica-Bold"),
        ])
        fd_table = Table(fd_data, colWidths=[7*cm, 6*cm, 2.5*cm])
        fd_table.setStyle(fd_style)
        story.append(fd_table)

    # ── Pie de página ────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.6*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
    story.append(Paragraph(
        'Nota: "Efectivo real en caja" considera ventas en efectivo + abonos, descontando ventas al fiado. '
        'Reporte generado automáticamente por Digital PyME.',
        note_style
    ))

    doc.build(story)
    return output_path
