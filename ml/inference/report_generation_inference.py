"""Rapor Üretimi — Template tabanlı (ilk sürüm).

Türkçe Lung-RADS 2022 yapılandırılmış rapor üretimi.
İlk sürüm: şablon tabanlı. Gelecek: Llama-3-8B-Instruct.

Bağımlılıklar: PyYAML
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

from ml.inference.base import BaseInferenceModel

logger = logging.getLogger(__name__)

LUNG_RADS_DESCRIPTIONS = {
    "1": "Negatif — Malignite bulgusu yok",
    "2": "Benign — İyi huylu özellikler",
    "3": "Muhtemelen benign — 6 ay kontrol",
    "4A": "Şüpheli (düşük) — 3 ay BT veya PET-BT",
    "4B": "Şüpheli (yüksek) — Biyopsi önerilir",
    "4X": "Ek bulgular — Multidisipliner kurul",
}

LUNG_RADS_RECOMMENDATIONS = {
    "1": "Yıllık DDBT taraması devam etmelidir.",
    "2": "Yıllık DDBT taraması devam etmelidir.",
    "3": "6 ay sonra kontrol BT önerilir.",
    "4A": "3 ay içinde kontrol BT veya PET-BT önerilir.",
    "4B": "Doku örnekleme / biyopsi önerilir.",
    "4X": "Multidisipliner kurul değerlendirmesi önerilir.",
}


class ReportGenerationInference(BaseInferenceModel):
    """Rapor Üretimi — template tabanlı.

    Mevcut mod: Template (şablon)
    - Pipeline çıktılarından yapılandırılmış Türkçe rapor
    - Lung-RADS 2022 kategorileri ve tavsiyeleri
    - Nodül detayları ve ölçümleri

    Gelecek mod: Llama-3-8B-Instruct (Q4_K_M)
    - Doğal dil Türkçe rapor üretimi
    - Bağlamsal tavsiyeler
    """

    _model = None
    _config: dict = {}
    _method: str = "template"

    REPORT_TEMPLATE = """AKCİĞER BT ANALİZ RAPORU — AlpCAN v{version}
{"=" * 50}
Tarih: {date}
Hasta ID: {patient_id}
Çalışma ID: {study_id}
Modalite: {modality}

KALİTE KONTROL
  Kalite Skoru: {quality_score}/100 — {quality_decision}

BULGULAR
{findings_text}

LUNG-RADS KATEGORİSİ: {lung_rads}
  {lung_rads_description}

TAVSİYE
  {recommendation}

{"=" * 50}
NOT: Bu rapor yapay zekâ destekli ön değerlendirmedir.
Nihai tanı kararı radyologa aittir.
AlpCAN — Akciğer Kanseri Erken Tespiti İçin YZ Karar Destek Platformu
"""

    @classmethod
    def load_model(cls, config: dict) -> None:
        """Rapor üretim modunu ayarla."""
        cls._config = config
        cls._method = config.get("method", "template")

        if cls._method == "llama_cpp":
            model_path = config.get("llama_model_path")
            if not model_path or not Path(model_path).exists():
                logger.warning(
                    "Llama-3 GGUF ağırlıkları bulunamadı, template moduna geri dönülüyor"
                )
                cls._method = "template"
            # Gelecek: from llama_cpp import Llama

        cls._model = True
        logger.info(f"Rapor üretimi hazır: method={cls._method}")

    @classmethod
    def predict(cls, pipeline_results: dict) -> dict:
        """Pipeline çıktılarından yapılandırılmış rapor oluştur.

        Args:
            pipeline_results: Pipeline çıktı dict'i:
                - nodules: list[dict] — nodül listesi
                - overall_lung_rads: str — genel Lung-RADS kategorisi
                - quality: dict — kalite kontrol sonuçları
                - patient_id: str
                - study_id: str

        Returns:
            {
                "report_text": str — tam rapor metni,
                "summary_tr": str — kısa Türkçe özet,
                "recommendation_tr": str — Türkçe tavsiye,
                "lung_rads": str,
            }
        """
        if not cls.is_loaded():
            cls.load_model({})

        if cls._method == "template":
            return cls._generate_template_report(pipeline_results)
        # Gelecek: return cls._generate_llm_report(pipeline_results)
        return cls._generate_template_report(pipeline_results)

    @classmethod
    def _generate_template_report(cls, data: dict) -> dict:
        """Şablon tabanlı rapor oluştur."""
        nodules = data.get("nodules", data.get("nodule_results", []))
        lung_rads = data.get("overall_lung_rads", "1")
        quality = data.get("quality", {})
        patient_id = data.get("patient_id", "ANON")
        study_id = data.get("study_id", "")

        # Nodül bulgularını metin olarak oluştur
        if nodules:
            findings_lines = []
            for i, nod in enumerate(nodules, 1):
                loc = nod.get("location_description", nod.get("location", "Belirtilmemiş"))
                diameter = nod.get("diameter_mm", 0)
                volume = nod.get("volume_mm3", 0)
                density = nod.get("density", "belirtilmemiş")
                mal_score = nod.get("malignancy_score", 0)
                nod_lr = nod.get("lung_rads", nod.get("lung_rads_category", ""))

                line = (
                    f"  Nodül {i}:\n"
                    f"    Lokalizasyon: {loc}\n"
                    f"    Boyut: {diameter:.1f} mm"
                )
                if volume:
                    line += f" (hacim: {volume:.1f} mm³)"
                line += f"\n    Yoğunluk: {density}"
                if mal_score:
                    line += f"\n    Malignite skoru: {mal_score:.2f}"
                if nod_lr:
                    lr_desc = LUNG_RADS_DESCRIPTIONS.get(nod_lr, "")
                    line += f"\n    Lung-RADS: {nod_lr} — {lr_desc}"

                findings_lines.append(line)

            findings_text = (
                f"  Toplam nodül sayısı: {len(nodules)}\n\n"
                + "\n\n".join(findings_lines)
            )
        else:
            findings_text = "  Nodül tespit edilmedi."

        # Özet ve tavsiye
        lung_rads_desc = LUNG_RADS_DESCRIPTIONS.get(lung_rads, "Belirtilmemiş")
        recommendation = LUNG_RADS_RECOMMENDATIONS.get(
            lung_rads, "Radyolog değerlendirmesi önerilir."
        )

        # Kısa özet oluştur
        if nodules:
            summary_parts = []
            for nod in nodules:
                diameter = nod.get("diameter_mm", 0)
                density = nod.get("density", "")
                loc = nod.get("location_description", nod.get("location", ""))
                nod_lr = nod.get("lung_rads", nod.get("lung_rads_category", ""))
                summary_parts.append(
                    f"{loc}'da {diameter:.1f} mm {density} nodül — Lung-RADS {nod_lr}"
                )
            summary_tr = ". ".join(summary_parts) + "."
        else:
            summary_tr = "Nodül tespit edilmedi. Normal bulgular."

        # Rapor metni
        report_text = (
            f"AKCİĞER BT ANALİZ RAPORU — AlpCAN v0.2.0\n"
            f"{'=' * 50}\n"
            f"Tarih: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}\n"
            f"Hasta ID: {patient_id}\n"
            f"Çalışma ID: {study_id}\n\n"
            f"KALİTE KONTROL\n"
            f"  Kalite Skoru: {quality.get('quality_score', 'N/A')}/100 "
            f"— {quality.get('decision', 'N/A')}\n\n"
            f"BULGULAR\n{findings_text}\n\n"
            f"LUNG-RADS KATEGORİSİ: {lung_rads}\n"
            f"  {lung_rads_desc}\n\n"
            f"TAVSİYE\n  {recommendation}\n\n"
            f"{'=' * 50}\n"
            f"NOT: Bu rapor yapay zekâ destekli ön değerlendirmedir.\n"
            f"Nihai tanı kararı radyologa aittir."
        )

        return {
            "report_text": report_text,
            "summary_tr": summary_tr,
            "recommendation_tr": recommendation,
            "lung_rads": lung_rads,
            "lung_rads_description": lung_rads_desc,
        }
