"""NB14 Rapor Motoru — yapılandırılmış Türkçe radyoloji raporu.

Birincil yöntem: ml/reporting/rapor_motoru.py (NB14 çıktısı)
Fallback: dahili şablon (rapor_motoru import edilemezse)

Kullanım:
    result = ReportGenerationInference.predict({
        "modalite": "BT",
        "hasta_id": "P001",
        "hasta_adi": "Ad Soyad",
        "yas": 55,
        "cinsiyet": "E",
        "bt_noduller": [
            {"lokalizasyon": "SAĞ ALT", "boyut_mm": 8.2,
             "lung_rads": "3", "malignite_skoru": 0.31}
        ]
    })
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ml.inference.base import BaseInferenceModel

logger = logging.getLogger(__name__)

_RAPOR_MOTORU_PATH = Path(__file__).parents[2] / "ml" / "reporting"

LUNG_RADS_TR = {
    "1":  "Negatif — Malignite bulgusu yok",
    "2":  "Benign — İyi huylu özellikler",
    "3":  "Muhtemelen benign — 6 ay kontrol",
    "4A": "Şüpheli (düşük) — 3 ay BT veya PET-BT",
    "4B": "Şüpheli (yüksek) — Biyopsi önerilir",
    "4X": "Ek bulgular — Multidisipliner kurul",
}
LUNG_RADS_RECOMMENDATION = {
    "1":  "Yıllık düşük doz BT taraması devam etmelidir.",
    "2":  "Yıllık düşük doz BT taraması devam etmelidir.",
    "3":  "6 ay sonra kontrol BT önerilir.",
    "4A": "3 ay içinde kontrol BT veya PET-BT önerilir.",
    "4B": "Doku örnekleme / biyopsi önerilir.",
    "4X": "Multidisipliner kurul değerlendirmesi önerilir.",
}

_LR_ORDER = {"1": 0, "2": 1, "3": 2, "4A": 3, "4B": 4, "4X": 5}


def _overall_lung_rads(nodules: list) -> str:
    """Nodül listesinden en yüksek Lung-RADS kategorisini al."""
    best = "1"
    for n in nodules:
        lr = str(n.get("lung_rads", n.get("lung_rads_category", "1")))
        if _LR_ORDER.get(lr, 0) > _LR_ORDER.get(best, 0):
            best = lr
    return best


def _pipeline_to_rapor_input(pipeline_results: dict) -> dict:
    """Pipeline çıktısını rapor_motoru.generate_report() formatına dönüştür."""
    nodules_raw = pipeline_results.get(
        "nodule_results",
        pipeline_results.get("nodules", [])
    )
    modalite = pipeline_results.get("modalite", "BT").upper()

    bt_noduller = []
    for n in nodules_raw:
        diam = n.get("diameter_mm", n.get("diameter_px", 0))
        lr   = str(n.get("lung_rads", n.get("lung_rads_category", "1")))
        cx, cy, cz = n.get("center", [0, 0, 0])[:3]

        # Basit sağ/sol lob lokalizasyonu (cx'e göre)
        volume = pipeline_results.get("volume")
        if volume is not None:
            lokalizasyon = "SAĞ AKCIĞER" if cx > volume.shape[2] / 2 else "SOL AKCIĞER"
        else:
            lokalizasyon = n.get("location_description", n.get("location", "Belirsiz"))

        bt_noduller.append({
            "lokalizasyon": lokalizasyon,
            "boyut_mm": round(float(diam), 1),
            "lung_rads": lr,
            "malignite_skoru": round(float(n.get("malignancy_score", 0)), 3),
            "malignite_sinif": n.get("malignancy_class", ""),
            "risk_sinifi": n.get("risk_class", ""),
            "koordinatlar": {"x": cx, "y": cy, "z": cz},
        })

    return {
        "modalite": modalite,
        "hasta_id": pipeline_results.get("patient_id", "ANON"),
        "hasta_adi": pipeline_results.get("patient_name", "Bilinmiyor"),
        "yas": pipeline_results.get("age", 0),
        "cinsiyet": pipeline_results.get("gender", "-"),
        "protokol_no": pipeline_results.get("study_id", ""),
        "klinik_bilgi": pipeline_results.get("clinical_info", ""),
        "bt_noduller": bt_noduller,
        "cxr_patolojiler": pipeline_results.get("cxr_pathologies", {}),
        "tarih": datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M"),
    }


class ReportGenerationInference(BaseInferenceModel):
    """NB14 rapor_motoru tabanlı Türkçe radyoloji raporu üretimi."""

    _model = None
    _generate_fn = None

    @classmethod
    def load_model(cls, config: dict) -> None:
        # rapor_motoru'nu dinamik import et
        if str(_RAPOR_MOTORU_PATH) not in sys.path:
            sys.path.insert(0, str(_RAPOR_MOTORU_PATH))
        try:
            import importlib
            rm = importlib.import_module("rapor_motoru")
            cls._generate_fn = rm.generate_report
            cls._model = True
            logger.info("NB14 rapor_motoru yüklendi")
        except ImportError:
            logger.warning("rapor_motoru import edilemedi — dahili şablon kullanılacak")
            cls._generate_fn = None
            cls._model = True

    @classmethod
    def predict(cls, pipeline_results: dict) -> dict:
        """Pipeline çıktısından yapılandırılmış Türkçe rapor üret.

        Args:
            pipeline_results: CT veya CXR pipeline sonuç dict'i

        Returns:
            {
                "report_text":       str,
                "summary_tr":        str,
                "recommendation_tr": str,
                "lung_rads":         str,
                "html":              str | None,
            }
        """
        if not cls.is_loaded():
            cls.load_model({})

        rapor_input = _pipeline_to_rapor_input(pipeline_results)

        # ── NB14 rapor_motoru (birincil) ───────────────────────────────────────
        if cls._generate_fn is not None:
            try:
                result = cls._generate_fn(rapor_input)
                return {
                    "report_text":       result.get("rapor_metni", result.get("text", "")),
                    "summary_tr":        result.get("ozet", result.get("bulgular", "")),
                    "recommendation_tr": result.get("takip", result.get("tavsiye", "")),
                    "lung_rads":         result.get("lung_rads", _overall_lung_rads(
                                            pipeline_results.get("nodule_results",
                                            pipeline_results.get("nodules", []))
                                         )),
                    "html":              result.get("html"),
                    "aciliyet":          result.get("aciliyet", "Normal"),
                }
            except Exception as e:
                logger.warning(f"rapor_motoru hatası, fallback: {e}")

        # ── Dahili şablon (fallback) ───────────────────────────────────────────
        return cls._template_report(pipeline_results, rapor_input)

    @classmethod
    def _template_report(cls, pipeline_results: dict, rapor_input: dict) -> dict:
        nodules = rapor_input.get("bt_noduller", [])
        lr = _overall_lung_rads(
            pipeline_results.get("nodule_results",
            pipeline_results.get("nodules", []))
        )

        if nodules:
            lines = [f"  {i+1}. {n['lokalizasyon']} — {n['boyut_mm']} mm "
                     f"(Lung-RADS {n['lung_rads']}, malignite: {n['malignite_skoru']:.2f})"
                     for i, n in enumerate(nodules)]
            findings = f"  {len(nodules)} nodül tespit edildi.\n" + "\n".join(lines)
            summary  = "; ".join(
                f"{n['lokalizasyon']} {n['boyut_mm']} mm" for n in nodules
            )
        else:
            findings = "  Nodül tespit edilmedi."
            summary  = "Normal bulgular, nodül yok."

        recommendation = LUNG_RADS_RECOMMENDATION.get(lr, "Radyolog değerlendirmesi.")
        report_text = (
            f"AKCİĞER BT ANALİZ RAPORU — AlpCAN\n"
            f"{'=' * 50}\n"
            f"Tarih: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}\n"
            f"Hasta ID: {rapor_input.get('hasta_id', 'ANON')}\n\n"
            f"BULGULAR\n{findings}\n\n"
            f"LUNG-RADS: {lr} — {LUNG_RADS_TR.get(lr, '')}\n\n"
            f"TAVSİYE\n  {recommendation}\n\n"
            f"{'=' * 50}\n"
            f"NOT: Yapay zekâ destekli ön değerlendirme. "
            f"Nihai tanı radyologa aittir."
        )
        return {
            "report_text":       report_text,
            "summary_tr":        summary,
            "recommendation_tr": recommendation,
            "lung_rads":         lr,
            "html":              None,
        }
