from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentResult:
    agent_name: str
    status: AgentStatus = AgentStatus.IDLE
    confidence: float | None = None
    findings: dict = field(default_factory=dict)
    pipeline_data: dict = field(default_factory=dict)
    duration_seconds: float = 0.0
    error_message: str | None = None


class BaseAgent(ABC):
    """Tüm AlpCAN YZ ajanlarının temel sınıfı.

    Her ajan 3 aşamadan geçer:
    1. preprocess() — Girdi verisini modele hazırla
    2. predict() — Model çıkarımı yap
    3. postprocess() — Sonuçları yapılandır
    """

    name: str = "BaseAgent"
    version: str = "0.1.0"
    requires_gpu: bool = False
    pipeline: str = "unknown"  # "ct" or "cxr"

    def run(self, input_data: dict) -> AgentResult:
        """Ajanı çalıştır — preprocess → predict → postprocess."""
        start_time = time.time()
        result = AgentResult(agent_name=self.name)

        try:
            result.status = AgentStatus.RUNNING
            logger.info(f"[{self.name}] Starting...")

            preprocessed = self.preprocess(input_data)
            prediction = self.predict(preprocessed)
            output = self.postprocess(prediction)

            result.status = AgentStatus.COMPLETED
            result.findings = output.get("findings", {})
            result.confidence = output.get("confidence")
            # Non-serializable pipeline pass-through (numpy arrays, etc.)
            result.pipeline_data = {
                k: v for k, v in output.items()
                if k not in ("findings", "confidence")
            }
            logger.info(f"[{self.name}] Completed successfully")

        except Exception as e:
            result.status = AgentStatus.ERROR
            result.error_message = str(e)
            logger.error(f"[{self.name}] Error: {e}")

        result.duration_seconds = round(time.time() - start_time, 3)
        return result

    @abstractmethod
    def preprocess(self, input_data: dict) -> dict:
        """Girdi verisini modele hazırla."""
        ...

    @abstractmethod
    def predict(self, preprocessed: dict) -> dict:
        """Model çıkarımı yap."""
        ...

    @abstractmethod
    def postprocess(self, prediction: dict) -> dict:
        """Sonuçları yapılandır. Dönen dict 'findings' ve 'confidence' içermeli."""
        ...

    def health_check(self) -> dict:
        """Ajan durumunu kontrol et."""
        return {
            "agent": self.name,
            "version": self.version,
            "requires_gpu": self.requires_gpu,
            "pipeline": self.pipeline,
            "status": "ready",
        }
