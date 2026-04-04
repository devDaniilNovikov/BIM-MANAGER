"""Export service — generates Excel, CSV, PDF files from report data."""

from __future__ import annotations

import csv
import io
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.report_builder import build_report


async def export_report(
    db: AsyncSession,
    project_id: uuid.UUID,
    report_type: str,
    fmt: str,
) -> io.BytesIO | None:
    # For "issues" report type, build it separately
    if report_type == "issues":
        data = await _build_issues_report(db, project_id)
    else:
        data = await build_report(db, project_id, report_type)

    if data is None:
        return None

    # Summary report has "sections" instead of flat columns/rows
    if "sections" in data:
        columns = []
        rows = []
        for section in data["sections"]:
            if rows:
                rows.append([])  # separator
            rows.append([section["title"]])
            rows.append(section["columns"])
            rows.extend(section["rows"])
        title = data.get("title", report_type)
    else:
        columns = data["columns"]
        rows = data["rows"]
        title = data.get("title", report_type)

    if fmt == "xlsx":
        return _to_xlsx(title, columns, rows)
    elif fmt == "csv":
        return _to_csv(columns, rows)
    elif fmt == "pdf":
        return _to_pdf(title, columns, rows)
    return None


def _to_xlsx(title: str, columns: list, rows: list) -> io.BytesIO:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]

    # Title row
    ws.append([title])
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(len(columns), 1))
    ws.cell(1, 1).font = Font(bold=True, size=14)
    ws.append([])

    # Header row
    if columns:
        ws.append(columns)
        header_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        for col_idx in range(1, len(columns) + 1):
            cell = ws.cell(3, col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

    # Data rows
    for row in rows:
        ws.append([str(v) if v is not None else "" for v in row])

    # Auto-width
    for col in ws.columns:
        max_len = 0
        column_letter = None
        for cell in col:
            if hasattr(cell, 'column_letter'):
                column_letter = cell.column_letter
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        if column_letter:
            ws.column_dimensions[column_letter].width = min(max_len + 2, 40)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def _to_csv(columns: list, rows: list) -> io.BytesIO:
    buf = io.StringIO()
    writer = csv.writer(buf)
    if columns:
        writer.writerow(columns)
    for row in rows:
        writer.writerow(row)
    result = io.BytesIO(buf.getvalue().encode("utf-8-sig"))
    result.seek(0)
    return result


def _to_pdf(title: str, columns: list, rows: list) -> io.BytesIO:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), topMargin=15 * mm, bottomMargin=15 * mm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 10 * mm))

    if not columns and not rows:
        story.append(Paragraph("Нет данных", styles["Normal"]))
        doc.build(story)
        buf.seek(0)
        return buf

    table_data = []
    if columns:
        table_data.append(columns)
    for row in rows:
        table_data.append([str(v) if v is not None else "" for v in row])

    if not table_data:
        story.append(Paragraph("Нет данных", styles["Normal"]))
        doc.build(story)
        buf.seek(0)
        return buf

    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E75B6")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4F8")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    doc.build(story)
    buf.seek(0)
    return buf


async def _build_issues_report(db: AsyncSession, project_id: uuid.UUID) -> dict | None:
    from sqlalchemy import select
    from app.models.project import Issue, Project

    project = await db.get(Project, project_id)
    if not project:
        return None

    stmt = (
        select(Issue)
        .where(Issue.project_id == project_id)
        .order_by(Issue.severity, Issue.created_at.desc())
    )
    result = await db.execute(stmt)
    issues = result.scalars().all()

    rows = []
    for i, issue in enumerate(issues, 1):
        rows.append([
            i,
            issue.severity,
            issue.category,
            issue.message,
            issue.status,
            issue.created_at.strftime("%Y-%m-%d %H:%M") if issue.created_at else "—",
        ])

    return {
        "title": "Журнал замечаний",
        "columns": ["№", "Критичность", "Категория", "Описание", "Статус", "Дата"],
        "rows": rows,
    }
