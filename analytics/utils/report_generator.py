import io
import base64
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def df_to_table_data(df, max_rows=20):
    df = df.head(max_rows)
    headers = list(df.columns)
    rows = [headers] + [list(map(str, row)) for row in df.values]
    return rows

def generate_pdf_report(insights, stats_df=None, state_filter=None, district_filter=None, chart_images=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=60, bottomMargin=40)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=18, textColor=colors.HexColor('#1a6b3c'), alignment=TA_CENTER)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor('#2c7be5'))
    body_style = styles['BodyText']

    story = []

    # Title
    story.append(Paragraph("Groundwater Analysis Report", title_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", body_style))
    if state_filter:
        story.append(Paragraph(f"State: {state_filter}", body_style))
    if district_filter:
        story.append(Paragraph(f"District: {district_filter}", body_style))
    story.append(Spacer(1, 0.3 * inch))

    # Insights
    story.append(Paragraph("Key Insights", heading_style))
    story.append(Spacer(1, 0.1 * inch))
    for insight in insights:
        story.append(Paragraph(f"• {insight}", body_style))
    story.append(Spacer(1, 0.3 * inch))

    # Stats table
    if stats_df is not None and not stats_df.empty:
        story.append(Paragraph("Summary Statistics", heading_style))
        story.append(Spacer(1, 0.1 * inch))
        table_data = df_to_table_data(stats_df.reset_index())
        t = Table(table_data, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c7be5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4ff')]),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3 * inch))

    # Charts
    if chart_images:
        story.append(Paragraph("Charts", heading_style))
        story.append(Spacer(1, 0.1 * inch))
        for img_b64 in chart_images:
            try:
                img_data = base64.b64decode(img_b64)
                img_buf = io.BytesIO(img_data)
                img = Image(img_buf, width=5 * inch, height=3 * inch)
                story.append(img)
                story.append(Spacer(1, 0.2 * inch))
            except Exception:
                pass

    doc.build(story)
    buffer.seek(0)
    return buffer
