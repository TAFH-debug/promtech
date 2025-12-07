import io
import os
import tempfile
import base64
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from sqlalchemy import func
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Frame,
    PageTemplate,
    NextPageTemplate,
    Image
)
from reportlab.graphics.shapes import Drawing, Rect, String
from PIL import Image as PILImage, ImageDraw, ImageFont
import folium
from app.api.deps import get_db
from app.models.object import Object
from app.models.inspection import Inspection
from app.models.defect import Defect

router = APIRouter()


class ReportRequest(BaseModel):
    map_image: Optional[str] = None

class ReportTheme:
    PRIMARY = colors.HexColor("#2C3E50")  
    ACCENT = colors.HexColor("#3498DB")     
    LIGHT_BG = colors.HexColor("#ECF0F1")  
    DANGER = colors.HexColor("#E74C3C")     
    WARNING = colors.HexColor("#F1C40F")  
    TEXT_MAIN = colors.HexColor("#2C3E50")
    TEXT_LIGHT = colors.white

def draw_header_footer(canvas, doc):
    """Рисует шапку и подвал на каждой странице"""
    canvas.saveState()
    
    canvas.setFillColor(ReportTheme.PRIMARY)
    canvas.rect(0, A4[1] - 20*mm, A4[0], 20*mm, fill=1, stroke=0)
    
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(colors.white)
    canvas.drawString(20*mm, A4[1] - 13*mm, "PIPELINE INSPECTION SYSTEM")
    
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(A4[0] - 20*mm, A4[1] - 13*mm, f"Generated: {datetime.now().strftime('%Y-%m-%d')}")

    canvas.setStrokeColor(ReportTheme.ACCENT)
    canvas.setLineWidth(1)
    canvas.line(20*mm, 15*mm, A4[0]-20*mm, 15*mm)
    
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.gray)
    page_num = canvas.getPageNumber()
    canvas.drawCentredString(A4[0]/2, 10*mm, f"Page {page_num}")
    
    canvas.restoreState()

def draw_cover_page(canvas, doc):
    """Специальный дизайн для первой страницы (Титульник)"""
    canvas.saveState()
    
    canvas.setFillColor(ReportTheme.PRIMARY)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    
    canvas.setFillColor(ReportTheme.ACCENT)
    canvas.rect(0, 0, A4[0], 60*mm, fill=1, stroke=0)
    
    canvas.restoreState()


def get_custom_styles():
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=ReportTheme.PRIMARY,
        spaceBefore=15,
        spaceAfter=10,
        borderPadding=(0, 0, 5, 0), 
        borderWidth=1,
        borderColor=colors.white, 
        fontName="Helvetica-Bold"
    ))
    
    styles.add(ParagraphStyle(
        name='NormalText',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#444444")
    ))
    
    styles.add(ParagraphStyle(
        name='CoverTitle',
        fontName="Helvetica-Bold",
        fontSize=32,
        leading=40,
        textColor=colors.white,
        alignment=TA_CENTER,
        spaceBefore=100*mm
    ))
    
    styles.add(ParagraphStyle(
        name='CoverSubTitle',
        fontName="Helvetica",
        fontSize=16,
        leading=20,
        textColor=colors.lightgrey,
        alignment=TA_CENTER,
        spaceBefore=10
    ))

    return styles

def build_cover(meta: Dict, styles) -> List:
    story = []
    pipeline_name = meta.get('pipeline_id', 'Unknown Pipeline')
    
    story.append(Paragraph("INSPECTION REPORT", styles["CoverTitle"]))
    story.append(Paragraph(f"Pipeline Object: {pipeline_name}", styles["CoverSubTitle"]))
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("Confidential Document", styles["CoverSubTitle"]))
    
    story.append(NextPageTemplate('NormalPage'))
    story.append(PageBreak())
    return story

def build_general_stats(defects: List[Dict], styles) -> List:
    story = []
    total = len(defects)
    avg_severity = sum(d["severity"] for d in defects) / total if total else 0
    critical = sum(1 for d in defects if d["severity"] >= 4)

    story.append(Paragraph("Executive Summary", styles["SectionHeader"]))
    
    kpi_data = [[
        f"{total}\nTotal Defects",
        f"{avg_severity:.1f}\nAvg Severity",
        f"{critical}\nCRITICAL"
    ]]
    
    kpi_table = Table(kpi_data, colWidths=[50*mm, 50*mm, 50*mm])
    kpi_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('TEXTCOLOR', (0,0), (1,0), ReportTheme.PRIMARY), 
        ('TEXTCOLOR', (2,0), (2,0), ReportTheme.DANGER), 
        ('BOX', (0,0), (0,0), 1, ReportTheme.LIGHT_BG),
        ('BOX', (1,0), (1,0), 1, ReportTheme.LIGHT_BG),
        ('BOX', (2,0), (2,0), 2, ReportTheme.DANGER),    
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
    ]))
    
    story.append(kpi_table)
    story.append(Spacer(1, 10*mm))
    return story

def build_defects_table(defects: List[Dict], styles) -> List:
    story = []
    story.append(Paragraph("Defects Registry", styles["SectionHeader"]))

    data = [["ID", "KM Mark", "Type", "Severity", "Coordinates"]]
    
    for d in defects:
        sev_display = str(d["severity"])
        coords = f"{d['coords'][0]:.4f}, {d['coords'][1]:.4f}"
        
        data.append([
            d["id"],
            f"{d['km_mark']:.2f}",
            d["type"],
            sev_display,
            coords
        ])

    col_widths = [30*mm, 30*mm, 40*mm, 20*mm, 50*mm]
    t = Table(data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), ReportTheme.PRIMARY), 
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ReportTheme.LIGHT_BG]), 
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]

    for i, d in enumerate(defects, start=1):
        if d["severity"] >= 4:
            style_cmds.append(('BACKGROUND', (3, i), (3, i), ReportTheme.DANGER))
            style_cmds.append(('TEXTCOLOR', (3, i), (3, i), colors.white))
            style_cmds.append(('FONTNAME', (3, i), (3, i), 'Helvetica-Bold'))
        elif d["severity"] == 3:
             style_cmds.append(('BACKGROUND', (3, i), (3, i), ReportTheme.WARNING))

    t.setStyle(TableStyle(style_cmds))
    story.append(t)
    return story

def generate_map_image(objects: List[Object], defects: List[Dict], pipeline_id: str) -> Optional[io.BytesIO]:
    """Генерирует статическую карту с объектами и дефектами используя folium и imgkit"""
    try:
        if not objects:
            return None
        
        # Получаем координаты всех объектов
        coords = [(float(obj.lat), float(obj.lon)) for obj in objects if obj.lat and obj.lon]
        if not coords:
            return None
        
        # Вычисляем центр карты
        avg_lat = sum(c[0] for c in coords) / len(coords)
        avg_lon = sum(c[1] for c in coords) / len(coords)
        
        # Создаем карту folium
        m = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=10,
            tiles='OpenStreetMap'
        )
        
        # Добавляем маркеры для объектов
        for obj in objects:
            if obj.lat and obj.lon:
                folium.Marker(
                    [float(obj.lat), float(obj.lon)],
                    popup=f"Object: {obj.object_id}",
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)
        
        # Добавляем маркеры для дефектов с цветами по критичности
        for defect in defects:
            lat, lon = defect['coords']
            if lat and lon and lat != 0.0 and lon != 0.0:
                severity = defect['severity']
                if severity >= 4:
                    color = 'red'
                    icon = 'exclamation-sign'
                elif severity == 3:
                    color = 'orange'
                    icon = 'warning-sign'
                else:
                    color = 'yellow'
                    icon = 'info-sign'
                
                folium.Marker(
                    [lat, lon],
                    popup=f"Defect: {defect['id']} (Severity: {severity})",
                    icon=folium.Icon(color=color, icon=icon)
                ).add_to(m)
        
        # Добавляем линию между объектами одного pipeline
        if len(coords) > 1:
            folium.PolyLine(
                coords,
                color='blue',
                weight=3,
                opacity=0.7
            ).add_to(m)
        
        # Сохраняем карту во временный HTML файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp_file:
            m.save(tmp_file.name)
            html_path = tmp_file.name
        
        try:
            # Пробуем использовать imgkit для конвертации HTML в изображение
            try:
                import imgkit
                # Настройки для imgkit
                options = {
                    'format': 'png',
                    'width': 1200,
                    'height': 800,
                    'disable-smart-shrinking': ''
                }
                
                # Конвертируем HTML в PNG
                screenshot_path = html_path.replace('.html', '.png')
                imgkit.from_file(html_path, screenshot_path, options=options)
                
                # Открываем изображение
                img = PILImage.open(screenshot_path)
                
                # Изменяем размер для PDF (ширина A4 минус отступы)
                max_width = int(A4[0] - 40*mm)
                max_height = int(200*mm)
                img.thumbnail((max_width, max_height), PILImage.Resampling.LANCZOS)
                
                # Сохраняем в BytesIO
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # Удаляем временные файлы
                os.unlink(html_path)
                os.unlink(screenshot_path)
                
                return img_buffer
            except (ImportError, Exception) as e:
                # Если imgkit не установлен или не работает, возвращаем None (будет использован placeholder)
                if os.path.exists(html_path):
                    os.unlink(html_path)
                print(f"imgkit not available or error: {e}")
                return None
        except Exception as e:
            # Если конвертация не работает, удаляем HTML файл и возвращаем None
            if os.path.exists(html_path):
                os.unlink(html_path)
            print(f"Error generating map screenshot: {e}")
            return None
    except Exception as e:
        print(f"Error generating map: {e}")
        return None

def build_site_map(objects: List[Object], defects: List[Dict], pipeline_id: str, styles, map_image_bytes: Optional[io.BytesIO] = None) -> List:
    """Создает секцию карты с реальной картой или placeholder"""
    story = []
    story.append(Paragraph("Visual Inspection Map", styles["SectionHeader"]))
    
    # Используем переданное изображение или генерируем новое
    map_image = map_image_bytes
    
    if map_image:
        # Вставляем изображение карты
        img = Image(map_image, width=A4[0] - 40*mm, height=200*mm)
        story.append(img)
        story.append(Spacer(1, 5))
        story.append(Paragraph("Map showing pipeline objects and detected defects.", styles["NormalText"]))
    else:
        # Fallback на placeholder
        drawing = Drawing(400, 150)
        rect = Rect(0, 0, 450, 150)
        rect.strokeColor = colors.gray
        rect.strokeDashArray = [4, 2]
        rect.fillColor = colors.HexColor("#f9f9f9")
        drawing.add(rect)
        
        text = String(225, 75, "MAP VISUALIZATION AREA", textAnchor="middle")
        text.fontName = "Helvetica-Bold"
        text.fillColor = colors.gray
        drawing.add(text)
        
        story.append(drawing)
        story.append(Spacer(1, 10))
        story.append(Paragraph("Note: Map data is generated based on sensor telemetry.", styles["NormalText"]))
    
    story.append(Spacer(1, 10*mm))
    return story


def _collect_defects_from_db(pipeline_id: str, db: Session) -> Tuple[List[Dict], List[Object], int]:
    needle = pipeline_id.strip()
    objects = db.exec(select(Object).where(func.lower(Object.pipeline_id) == needle.lower())).all()
    if not objects:
        raise HTTPException(status_code=404, detail=f"No objects found for pipeline '{pipeline_id}'")

    object_ids = [obj.object_id for obj in objects if obj.object_id is not None]
    inspections = []
    defects = []

    if object_ids:
        inspections = db.exec(select(Inspection).where(Inspection.object_id.in_(object_ids))).all()
        insp_ids = [i.inspection_id for i in inspections if i.inspection_id is not None]
        if insp_ids:
            defects = db.exec(select(Defect).where(Defect.inspection_id.in_(insp_ids))).all()

    collected = []
    obj_lookup = {o.object_id: o for o in objects}
    
    for idx, defect in enumerate(defects, start=1):
        insp = next((i for i in inspections if i.inspection_id == defect.inspection_id), None)
        obj = obj_lookup.get(insp.object_id) if insp else None
        
        severity = 1
        if defect.depth:
            depth_val = float(defect.depth)
            if depth_val >= 5:
                severity = 5
            elif depth_val >= 3:
                severity = 4
            elif depth_val >= 2:
                severity = 3
            elif depth_val >= 1:
                severity = 2
            else:
                severity = 1
            
        collected.append({
            "id": f"D-{defect.defect_id or idx:03d}",
            "km_mark": float(idx * 0.5), # Mock KM
            "type": defect.defect_type or "General",
            "severity": severity,
            "coords": (float(obj.lat) if obj else 0.0, float(obj.lon) if obj else 0.0),
        })
    return collected, list(objects), len(objects)

@router.post("/{pipeline_id}/pdf", response_class=StreamingResponse)
def pipeline_report_pdf(
    pipeline_id: str,
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    defects, objects, obj_count = _collect_defects_from_db(pipeline_id, db)
    meta = {"pipeline_id": pipeline_id, "object_count": obj_count}

    # Обрабатываем переданное изображение карты
    map_image_bytes = None
    map_image = request.map_image
    if map_image:
        try:
            # Добавляем padding если нужно (base64 должен быть кратен 4)
            missing_padding = len(map_image) % 4
            if missing_padding:
                map_image += '=' * (4 - missing_padding)
            
            # Декодируем base64
            image_data = base64.b64decode(map_image, validate=True)
            # Открываем изображение и изменяем размер
            img = PILImage.open(io.BytesIO(image_data))
            # Изменяем размер для PDF
            max_width = int(A4[0] - 40*mm)
            max_height = int(200*mm)
            img.thumbnail((max_width, max_height), PILImage.Resampling.LANCZOS)
            # Сохраняем в BytesIO
            map_image_bytes = io.BytesIO()
            img.save(map_image_bytes, format='PNG')
            map_image_bytes.seek(0)
        except Exception as e:
            print(f"Error processing map image: {e}")
            import traceback
            traceback.print_exc()
            map_image_bytes = None
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            rightMargin=20*mm, leftMargin=20*mm, 
                            topMargin=20*mm, bottomMargin=20*mm)
    frame_normal = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height - 20*mm, id='normal')
    frame_cover = Frame(0, 0, A4[0], A4[1], id='cover') # На весь лист

    template_cover = PageTemplate(id='CoverPage', frames=frame_cover, onPage=draw_cover_page)
    template_normal = PageTemplate(id='NormalPage', frames=frame_normal, onPage=draw_header_footer)
    
    doc.addPageTemplates([template_cover, template_normal])

    styles = get_custom_styles()
    story = []
    
    story += build_cover(meta, styles)
    
    story += build_general_stats(defects, styles)
    story += build_site_map(objects, defects, pipeline_id, styles, map_image_bytes)
    story += build_defects_table(defects, styles)

    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Report_{pipeline_id}.pdf"'}
    )
