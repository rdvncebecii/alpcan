"""Pipeline 1 — CXR Otomatik Tarama

4 model ensemble ile akciğer röntgeni analizi.
Ensemble oylama: 4/4 → acil BT, 3/4 → 2 hafta BT, 2/4 → radyolog, 1/4 → kayıt, 0/4 → normal.
"""

import logging
from app.agents.agent10_cxr_quality import CXRQualityAgent
from app.agents.agent07a_ark import ArkAgent
from app.agents.agent07b_torchxray import TorchXRayAgent
from app.agents.agent07c_xraydar import XRaydarAgent
from app.agents.agent07d_medrax import MedRAXAgent
from app.agents.base import AgentResult

logger = logging.getLogger(__name__)

ENSEMBLE_DECISIONS = {
    4: {"priority": "YÜKSEK ÖNCELİK", "action": "Acil BT önerisi — radyologa anlık uyarı"},
    3: {"priority": "ORTA-YÜKSEK ÖNCELİK", "action": "2 hafta içinde BT önerilir"},
    2: {"priority": "ORTA ÖNCELİK", "action": "Radyolog değerlendirmesi istenir"},
    1: {"priority": "DÜŞÜK ÖNCELİK", "action": "Kayıt altına alınır, takip hatırlatıcı"},
    0: {"priority": "NORMAL", "action": "Rutin akış devam eder"},
}


class CXRPipeline:
    """CXR analiz pipeline'ı — 4 model ensemble + kalite kontrol."""

    def __init__(self):
        self.quality_agent = CXRQualityAgent()
        self.models = [
            ArkAgent(),
            TorchXRayAgent(),
            XRaydarAgent(),
            MedRAXAgent(),
        ]

    def run(self, input_data: dict) -> dict:
        """Tam CXR pipeline'ını çalıştır."""
        results: list[AgentResult] = []

        # 1. Kalite kontrol
        qc_result = self.quality_agent.run(input_data)
        results.append(qc_result)

        if qc_result.findings.get("decision") == "RED":
            logger.warning("CXR kalite kontrolü RED — pipeline durduruluyor")
            return {
                "status": "quality_rejected",
                "quality": qc_result.findings,
                "agent_results": [r.__dict__ for r in results],
            }

        # 2. 4 model ensemble
        suspicious_votes = 0
        model_votes = {}

        for model in self.models:
            result = model.run(input_data)
            results.append(result)
            is_suspicious = result.findings.get("is_suspicious", False)
            model_votes[model.name] = is_suspicious
            if is_suspicious:
                suspicious_votes += 1

        # 3. Ensemble karar
        decision = ENSEMBLE_DECISIONS.get(suspicious_votes, ENSEMBLE_DECISIONS[0])

        return {
            "status": "completed",
            "suspicious_votes": suspicious_votes,
            "total_models": 4,
            "model_votes": model_votes,
            "priority": decision["priority"],
            "recommendation": decision["action"],
            "quality": qc_result.findings,
            "agent_results": [r.__dict__ for r in results],
        }
