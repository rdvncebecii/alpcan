"""Rapor endpoint'leri — Lung-RADS raporları."""

import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.study import Study
router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class NoduleFinding(BaseModel):
    id: str
    location: str | None = None
    size_mm: float
    volume_mm3: float | None = None
    density: str | None = None
    lung_rads: str | None = None
    malignancy_score: float | None = None
    recommendation: str | None = None


class LungRADSReport(BaseModel):
    study_id: str
    patient_id: str
    report_date: datetime
    overall_lung_rads: str
    nodules: list[NoduleFinding] = []
    cxr_ensemble_score: float | None = None
    cxr_recommendation: str | None = None
    summary_tr: str | None = None
    recommendation_tr: str | None = None
    full_report_tr: str | None = None
    total_processing_seconds: float | None = None
    edited: bool = False


class ReportUpdateRequest(BaseModel):
    summary_tr: str | None = None
    recommendation_tr: str | None = None
    full_report_tr: str | None = None


# ── GET /{study_id} ──────────────────────────────────────────────────────────

@router.get("/{study_id}", response_model=LungRADSReport)
async def get_report(study_id: str, db: AsyncSession = Depends(get_db)):
    """Çalışma için Lung-RADS raporunu getir."""
    result = await db.execute(
        select(Study)
        .options(
            selectinload(Study.report),
            selectinload(Study.nodules),
            selectinload(Study.patient),
        )
        .where(Study.id == study_id)
    )
    study = result.scalar_one_or_none()

    if not study:
        raise HTTPException(status_code=404, detail="Çalışma bulunamadı")

    if not study.report:
        raise HTTPException(
            status_code=404,
            detail="Rapor henüz oluşturulmadı. Önce analiz başlatın.",
        )

    report = study.report
    nodule_findings = [
        NoduleFinding(
            id=n.id,
            location=n.location_description,
            size_mm=n.diameter_mm,
            volume_mm3=n.volume_mm3,
            density=n.density,
            lung_rads=n.lung_rads_category,
            malignancy_score=n.malignancy_score,
        )
        for n in (study.nodules or [])
    ]

    return LungRADSReport(
        study_id=study.id,
        patient_id=study.patient_id,
        report_date=report.created_at,
        overall_lung_rads=report.overall_lung_rads,
        nodules=nodule_findings,
        cxr_ensemble_score=report.cxr_ensemble_score,
        cxr_recommendation=report.cxr_recommendation,
        summary_tr=report.summary_tr,
        recommendation_tr=report.recommendation_tr,
        full_report_tr=report.full_report_tr,
        total_processing_seconds=report.total_processing_seconds,
        edited=bool(report.lung_rads_details and report.lung_rads_details.get("edited")),
    )


# ── PUT /{study_id} — Rapor düzenle ─────────────────────────────────────────

@router.put("/{study_id}", response_model=LungRADSReport)
async def update_report(
    study_id: str,
    body: ReportUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Rapor metnini güncelle (Radyolog düzenleme)."""
    result = await db.execute(
        select(Study)
        .options(
            selectinload(Study.report),
            selectinload(Study.nodules),
            selectinload(Study.patient),
        )
        .where(Study.id == study_id)
    )
    study = result.scalar_one_or_none()

    if not study:
        raise HTTPException(status_code=404, detail="Çalışma bulunamadı")

    if not study.report:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı")

    report = study.report

    if body.summary_tr is not None:
        report.summary_tr = body.summary_tr
    if body.recommendation_tr is not None:
        report.recommendation_tr = body.recommendation_tr
    if body.full_report_tr is not None:
        report.full_report_tr = body.full_report_tr

    # Düzenlendi işareti
    details = report.lung_rads_details or {}
    details["edited"] = True
    details["edited_at"] = datetime.utcnow().isoformat()
    report.lung_rads_details = details

    await db.commit()
    await db.refresh(report)

    nodule_findings = [
        NoduleFinding(
            id=n.id,
            location=n.location_description,
            size_mm=n.diameter_mm,
            volume_mm3=n.volume_mm3,
            density=n.density,
            lung_rads=n.lung_rads_category,
            malignancy_score=n.malignancy_score,
        )
        for n in (study.nodules or [])
    ]

    return LungRADSReport(
        study_id=study.id,
        patient_id=study.patient_id,
        report_date=report.created_at,
        overall_lung_rads=report.overall_lung_rads,
        nodules=nodule_findings,
        cxr_ensemble_score=report.cxr_ensemble_score,
        cxr_recommendation=report.cxr_recommendation,
        summary_tr=report.summary_tr,
        recommendation_tr=report.recommendation_tr,
        full_report_tr=report.full_report_tr,
        total_processing_seconds=report.total_processing_seconds,
        edited=True,
    )


# ── GET /{study_id}/pdf ──────────────────────────────────────────────────────

@router.get("/{study_id}/pdf")
async def download_report_pdf(study_id: str, db: AsyncSession = Depends(get_db)):
    """Raporu PDF olarak indir (reportlab ile oluştur)."""
    result = await db.execute(
        select(Study)
        .options(
            selectinload(Study.report),
            selectinload(Study.nodules),
            selectinload(Study.patient),
        )
        .where(Study.id == study_id)
    )
    study = result.scalar_one_or_none()

    if not study or not study.report:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı")

    # Kayıtlı PDF varsa direkt sun
    if study.report.pdf_path:
        try:
            from fastapi.responses import FileResponse
            return FileResponse(study.report.pdf_path, media_type="application/pdf")
        except Exception:
            pass  # Dosya yoksa yeniden oluştur

    # reportlab ile PDF oluştur
    try:
        pdf_bytes = _build_pdf(study)
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="PDF oluşturmak için 'reportlab' kütüphanesi gerekli. pip install reportlab",
        )

    filename = f"alpcan_rapor_{study.patient.anonymous_id if study.patient else study_id[:8]}_{study_id[:8]}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_pdf(study) -> bytes:
    """Reportlab ile Lung-RADS PDF raporu oluştur."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    tl_color = colors.HexColor("#1a9fa8")

    style_title = ParagraphStyle(
        "title", parent=styles["Heading1"],
        fontSize=20, textColor=tl_color, spaceAfter=4,
    )
    style_sub = ParagraphStyle(
        "sub", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#888888"), spaceAfter=12,
    )
    style_section = ParagraphStyle(
        "section", parent=styles["Heading2"],
        fontSize=11, textColor=tl_color, spaceBefore=14, spaceAfter=4,
        borderPad=2,
    )
    style_body = ParagraphStyle(
        "body", parent=styles["Normal"],
        fontSize=10, leading=16, textColor=colors.HexColor("#222222"),
    )
    style_small = ParagraphStyle(
        "small", parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#666666"),
    )

    report = study.report
    patient_name = study.patient.anonymous_id if study.patient else "Bilinmiyor"
    study_date = study.study_date.strftime("%d.%m.%Y") if study.study_date else "—"
    now_str = datetime.utcnow().strftime("%d.%m.%Y %H:%M")

    # Lung-RADS renk
    rads_colors = {
        "1": colors.HexColor("#2dd88a"),
        "2": colors.HexColor("#2dd88a"),
        "3": colors.HexColor("#e8a82e"),
        "4A": colors.HexColor("#e8692e"),
        "4B": colors.HexColor("#e8453f"),
        "4X": colors.HexColor("#e8453f"),
    }
    rads_color = rads_colors.get(report.overall_lung_rads, colors.grey)

    elements = []

    # Header
    elements.append(Paragraph("AlpCAN", style_title))
    elements.append(Paragraph(
        "Akciğer Kanseri Erken Tespit Platformu — Radyoloji Raporu",
        style_sub,
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=tl_color, spaceAfter=12))

    # Hasta bilgileri
    info_data = [
        ["Hasta ID", patient_name, "Çalışma Tarihi", study_date],
        ["Modalite", study.modality, "Rapor Tarihi", now_str],
        ["Çalışma ID", str(study.id)[:16] + "...", "Pipeline", study.pipeline_type or "—"],
    ]
    info_table = Table(info_data, colWidths=[3.5 * cm, 5 * cm, 3.5 * cm, 5 * cm])
    info_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#888888")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#888888")),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTNAME", (3, 0), (3, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e0e0e0")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 12))

    # Lung-RADS kutusu
    rads_data = [[
        Paragraph(f"<b>Lung-RADS {report.overall_lung_rads}</b>", ParagraphStyle(
            "rads", parent=styles["Normal"],
            fontSize=16, textColor=rads_color,
        )),
        Paragraph(
            _rads_name(report.overall_lung_rads),
            ParagraphStyle("radsn", parent=styles["Normal"], fontSize=10, textColor=rads_color),
        ),
    ]]
    rads_table = Table(rads_data, colWidths=[6 * cm, 11 * cm])
    rads_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fffe")),
        ("LINEABOVE", (0, 0), (-1, 0), 2, rads_color),
        ("LINEBELOW", (0, 0), (-1, 0), 2, rads_color),
        ("PADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(rads_table)
    elements.append(Spacer(1, 12))

    # Bulgular
    if report.summary_tr:
        elements.append(Paragraph("BULGULAR", style_section))
        elements.append(Paragraph(report.summary_tr, style_body))

    # Öneri
    if report.recommendation_tr:
        elements.append(Paragraph("KLİNİK ÖNERİ", style_section))
        elements.append(Paragraph(report.recommendation_tr, style_body))

    # Nodüller
    nodules = study.nodules or []
    if nodules:
        elements.append(Paragraph("NODÜL BULGULARI", style_section))
        nod_data = [["#", "Lokasyon", "Çap (mm)", "Hacim (mm³)", "Dansitite", "RADS", "Malignite %"]]
        for i, n in enumerate(nodules, 1):
            mal_pct = f"{n.malignancy_score * 100:.0f}%" if n.malignancy_score is not None else "—"
            nod_data.append([
                str(i),
                n.location_description or "—",
                f"{n.diameter_mm:.1f}",
                f"{n.volume_mm3:.0f}" if n.volume_mm3 else "—",
                n.density or "—",
                n.lung_rads_category or "—",
                mal_pct,
            ])
        nod_table = Table(nod_data, colWidths=[0.6 * cm, 5.5 * cm, 1.8 * cm, 2 * cm, 2 * cm, 1.5 * cm, 2.2 * cm])
        nod_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), tl_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ]))
        elements.append(nod_table)

    # CXR Ensemble
    if report.cxr_ensemble_score is not None:
        elements.append(Paragraph("CXR ENSEMBLE ANALİZİ", style_section))
        cxr_text = f"Ensemble Skor: {report.cxr_ensemble_score * 100:.0f}%"
        if report.cxr_recommendation:
            cxr_text += f" — {report.cxr_recommendation}"
        elements.append(Paragraph(cxr_text, style_body))

    # İşlem süresi
    if report.total_processing_seconds:
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(
            f"İşlem süresi: {report.total_processing_seconds:.1f} saniye",
            style_small,
        ))

    # Footer
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=8))
    elements.append(Paragraph(
        f"Bu rapor AlpCAN YZ sistemi tarafından üretilmiştir. Nihai tanı sorumluluğu radyoloji uzmanına aittir. "
        f"Rapor tarihi: {now_str}",
        style_small,
    ))

    doc.build(elements)
    return buffer.getvalue()


def _rads_name(rads: str) -> str:
    names = {
        "1": "Negatif — Yıllık tarama yeterli",
        "2": "Benign Görünüm — Yıllık tarama yeterli",
        "3": "Muhtemelen Benign — 6 ay sonra DDBT kontrolü",
        "4A": "Şüpheli (Düşük Risk) — 3 ay sonra DDBT kontrolü",
        "4B": "Şüpheli (Yüksek Risk) — Biyopsi / Cerrahi konsültasyon",
        "4X": "Ek Bulgularla Yüksek Şüphe — İleri tetkik gerekli",
    }
    return names.get(rads, "Bilinmiyor")
