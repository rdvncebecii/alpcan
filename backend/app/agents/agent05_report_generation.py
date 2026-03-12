"""Ajan 5 — Rapor Üretimi: Meta-Llama-3-8B-Instruct (llama.cpp Q4_K_M)

Türkçe Lung-RADS 2022 yapılandırılmış rapor üretimi.
Çıktı: PDF + DICOM SR + HL7 FHIR R4 DocumentReference.
CPU ile ~10-30 s/rapor, GPU ile ~3-8 s.
"""

from app.agents.base import BaseAgent


class ReportGenerationAgent(BaseAgent):
    name = "Report Generation (Llama-3)"
    version = "0.1.0"
    requires_gpu = False  # CPU yeterli (Q4 quantized)
    pipeline = "ct"

    REPORT_TEMPLATE = """
AKCIĞER BT ANALİZ RAPORU — AlpCAN v{version}
==============================================
Tarih: {date}
Hasta ID: {patient_id}

BULGULAR:
{findings_text}

LUNG-RADS KATEGORİSİ: {lung_rads}
{lung_rads_description}

TAVSİYE:
{recommendation}

NOT: Bu rapor yapay zekâ destekli ön değerlendirmedir.
Nihai tanı kararı radyologa aittir.
"""

    def preprocess(self, input_data: dict) -> dict:
        """Tüm ajan çıktılarını rapor prompt'una dönüştür."""
        # TODO: Tüm pipeline çıktılarını topla
        return {
            "nodules": input_data.get("nodules", []),
            "lung_rads": input_data.get("overall_lung_rads", "1"),
            "growth_data": input_data.get("growth_results", []),
            "quality_score": input_data.get("quality_score", 100),
            "status": "stub",
        }

    def predict(self, preprocessed: dict) -> dict:
        """Llama-3 ile Türkçe rapor oluştur."""
        # TODO: llama.cpp ile rapor üretimi
        lung_rads = preprocessed.get("lung_rads", "1")
        return {
            "report_text": self.REPORT_TEMPLATE.format(
                version=self.version,
                date="2026-03-12",
                patient_id="ANON-001",
                findings_text="Stub rapor — model entegre edildiğinde detaylı bulgular burada yer alacaktır.",
                lung_rads=lung_rads,
                lung_rads_description="Stub açıklama",
                recommendation="Stub tavsiye",
            ),
            "status": "stub",
        }

    def postprocess(self, prediction: dict) -> dict:
        """PDF, DICOM SR ve FHIR çıktıları oluştur."""
        return {
            "findings": {
                "report_text": prediction.get("report_text", ""),
                "pdf_generated": False,
                "dicom_sr_generated": False,
                "fhir_document_created": False,
            },
            "confidence": 1.0,
        }
