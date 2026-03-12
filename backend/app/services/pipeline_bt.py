"""Pipeline 2 — BT Tam Analiz (6 Ajan)

Sıralı pipeline: QC → Ön İşleme → Nodül Tespit → Karakterizasyon → Büyüme Takibi → Rapor.
Her BT tüm 6 ajandan geçer.
"""

import logging
from app.agents.agent06_ct_quality import CTQualityAgent
from app.agents.agent01_preprocess import PreprocessAgent
from app.agents.agent02_nodule_detection import NoduleDetectionAgent
from app.agents.agent03_characterization import CharacterizationAgent
from app.agents.agent04_growth_tracking import GrowthTrackingAgent
from app.agents.agent05_report_generation import ReportGenerationAgent
from app.agents.base import AgentResult

logger = logging.getLogger(__name__)


class BTPipeline:
    """BT analiz pipeline'ı — 6 ajan sıralı çalışır."""

    def __init__(self):
        self.agents = [
            CTQualityAgent(),
            PreprocessAgent(),
            NoduleDetectionAgent(),
            CharacterizationAgent(),
            GrowthTrackingAgent(),
            ReportGenerationAgent(),
        ]

    def run(self, input_data: dict) -> dict:
        """Tam BT pipeline'ını çalıştır."""
        results: list[AgentResult] = []
        pipeline_data = input_data.copy()

        for agent in self.agents:
            logger.info(f"Running agent: {agent.name}")
            result = agent.run(pipeline_data)
            results.append(result)

            # Kalite kontrol RED ise durdur
            if agent.name == "CT Quality Control":
                if result.findings.get("decision") == "RED":
                    logger.warning("BT kalite kontrolü RED — pipeline durduruluyor")
                    return {
                        "status": "quality_rejected",
                        "quality": result.findings,
                        "agent_results": [r.__dict__ for r in results],
                    }

            # Her ajanın çıktısını bir sonrakine aktar
            if result.findings:
                pipeline_data.update(result.findings)

        # Son rapor ajanının çıktısı
        report_result = results[-1]

        return {
            "status": "completed",
            "nodule_count": pipeline_data.get("nodule_count", 0),
            "overall_lung_rads": pipeline_data.get("overall_lung_rads", "1"),
            "report": report_result.findings,
            "quality": results[0].findings,
            "agent_results": [r.__dict__ for r in results],
        }
