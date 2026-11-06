import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generar_excel_estilizado(datos_por_dispositivo):
    wb = Workbook()
    wb.remove(wb.active) # Eliminamos la hoja vacía por defecto

    fill_header = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    font_header = Font(name="Calibri", size=11, bold=True, color="38BDF8")
    fill_par = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    fill_impar = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    borde_fino = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )

    for dev_id, info in datos_por_dispositivo.items():
        ws = wb.create_sheet(title=f"Nodo_{dev_id[:20]}")
        ws.views.sheetView[0].showGridLines = True

        # Encabezado corporativo del dispositivo
        ws.merge_cells("A1:F1")
        ws["A1"] = f"🍃 REPORTE DE MEDICIONES - DISPOSITIVO: {dev_id.upper()}"
        ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
        ws["A1"].fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 30

        # Metadatos del dispositivo
        ws["A3"] = "Nombre:"; ws["B3"] = info.get("nombre", "Prototipo")
        ws["C3"] = "Ubicación:"; ws["D3"] = info.get("ubicacion", "General")
        ws["E3"] = "Muestra:"; ws["F3"] = f"Últimas {len(info['filas'])} lecturas"
        for col_meta in ["A3", "C3", "E3"]:
            ws[col_meta].font = Font(bold=True, color="475569")

        # Encabezados de tabla
        encabezados = ["Fecha y Hora Local", "Temp (°C)", "Humedad (%)", "Presión (hPa)", "PM 2.5 (µg/m³)", "PM 10 (µg/m³)"]
        ws.append([]) # Fila 4 vacía
        ws.append(encabezados) # Fila 5
        ws.row_dimensions[5].height = 24

        for col_idx in range(1, 7):
            c = ws.cell(row=5, column=col_idx)
            c.fill = fill_header
            c.font = font_header
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = borde_fino

        for i, f in enumerate(info["filas"], start=6):
            ws.append([f["fecha_hora"], f["temperatura"], f["humedad"], f["presion"], f["pm25"], f["pm10"]])
            ws.row_dimensions[i].height = 20
            f_actual = fill_par if i % 2 == 0 else fill_impar
            for col_idx in range(1, 7):
                celda = ws.cell(row=i, column=col_idx)
                celda.fill = f_actual
                celda.border = borde_fino
                celda.alignment = Alignment(horizontal="center", vertical="center")

        for idx in range(1, 7):
            letra = get_column_letter(idx)
            max_len = max(len(str(ws.cell(row=r, column=idx).value or "")) for r in range(5, ws.max_row + 1))
            ws.column_dimensions[letra].width = max(max_len + 4, 14)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def generar_pdf_estilizado(datos_por_dispositivo):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elementos = []
    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle('Titulo', parent=estilos['Heading1'], fontSize=16, textColor=colors.HexColor("#0F172A"), spaceAfter=4)
    estilo_sub = ParagraphStyle('Sub', parent=estilos['Normal'], fontSize=9, textColor=colors.HexColor("#64748B"), spaceAfter=14)
    estilo_dev = ParagraphStyle('DevHead', parent=estilos['Heading2'], fontSize=12, textColor=colors.HexColor("#0284C7"), spaceBefore=10, spaceAfter=4)

    elementos.append(Paragraph("<b>Reporte de Monitoreo Ambiental | Red IoT</b>", estilo_titulo))
    elementos.append(Paragraph("Auditoría técnica de las últimas 50 mediciones por dispositivo | Base de datos SQLite", estilo_sub))

    for dev_id, info in datos_por_dispositivo.items():
        elementos.append(Paragraph(f"<b>Dispositivo: {dev_id}</b> ({info.get('nombre', 'Prototipo')}) — Ubicación: {info.get('ubicacion', 'General')}", estilo_dev))
        elementos.append(Spacer(1, 4))

        datos_tabla = [["Fecha y Hora", "Temp", "Humedad", "Presión", "PM 2.5", "PM 10"]]
        for f in info["filas"]:
            datos_tabla.append([
                str(f["fecha_hora"]),
                f"{f['temperatura'] or '--'} °C",
                f"{f['humedad'] or '--'} %",
                f"{f['presion'] or '--'} hPa",
                f"{f['pm25'] or '--'}",
                f"{f['pm10'] or '--'}"
            ])

        t = Table(datos_tabla, colWidths=[130, 75, 75, 80, 70, 70])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#38BDF8")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elementos.append(t)
        elementos.append(Spacer(1, 14))

    doc.build(elementos)
    buf.seek(0)
    return buf
