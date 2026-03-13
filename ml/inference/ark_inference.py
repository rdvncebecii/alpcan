"""Ark+ Foundation Model (Swin Transformer Large) — 14 patoloji tespiti.

Notebook 05 (cell 10-15) birebir alınan inference mantığı.
Ağırlıklar Kaggle dataset veya Dropbox'tan sağlanır.

KRİTİK: timm==0.5.4 ZORUNLU — sonraki sürümler Swin mimarisini bozar.

Bağımlılıklar: torch, timm==0.5.4, numpy, PIL
"""

import logging
from pathlib import Path
from typing import Any

import numpy as np

from ml.inference.base import BaseInferenceModel, ModelNotAvailableError

logger = logging.getLogger(__name__)

# NIH14 etiket sırası (head_n=2 çıkış sırası)
NIH14_LABELS = [
    "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration",
    "Mass", "Nodule", "Pneumonia", "Pneumothorax",
    "Consolidation", "Edema", "Emphysema", "Fibrosis",
    "Pleural_Thickening", "Hernia",
]


def _build_ark_model(config: dict) -> "ArkSwinTransformer":
    """ArkSwinTransformer modelini oluştur.

    Notebook 05, cell 10-11'den birebir.
    """
    import torch.nn as nn
    import timm.models.swin_transformer as swin

    num_classes_list = config.get("num_classes_list", [14, 14, 14, 3, 6, 1])
    projector_features = config.get("projector_features", 1376)
    use_mlp = config.get("use_mlp", False)

    class ArkSwinTransformer(swin.SwinTransformer):
        """Ark+ (Foundation Ark) Swin Transformer Large modeli.

        6 dataset üzerinde omni-label pre-trained:
          - MIMIC-CXR (14 sınıf)
          - CheXpert (14 sınıf)
          - NIH ChestX-ray14 (14 sınıf) → head_n=2
          - RSNA Pneumonia (3 sınıf)
          - VinDr-CXR (6 sınıf)
          - Shenzhen TB (1 sınıf)
        """

        def __init__(self, ncl, pf, umlp, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.projector = None
            if pf:
                encoder_features = self.num_features
                self.num_features = pf
                if umlp:
                    self.projector = nn.Sequential(
                        nn.Linear(encoder_features, self.num_features),
                        nn.ReLU(inplace=True),
                        nn.Linear(self.num_features, self.num_features),
                    )
                else:
                    self.projector = nn.Linear(encoder_features, self.num_features)
            self.omni_heads = nn.ModuleList([
                nn.Linear(self.num_features, nc) if nc > 0 else nn.Identity()
                for nc in ncl
            ])

        def forward(self, x, head_n=None):
            x = self.forward_features(x)
            if self.projector:
                x = self.projector(x)
            if head_n is not None:
                return x, self.omni_heads[head_n](x)
            return [head(x) for head in self.omni_heads]

        def generate_embeddings(self, x, after_proj=True):
            x = self.forward_features(x)
            if after_proj and self.projector:
                x = self.projector(x)
            return x

    model = ArkSwinTransformer(
        ncl=num_classes_list,
        pf=projector_features,
        umlp=use_mlp,
        img_size=config.get("img_size", 768),
        patch_size=config.get("patch_size", 4),
        window_size=config.get("window_size", 12),
        embed_dim=config.get("embed_dim", 192),
        depths=tuple(config.get("depths", [2, 2, 18, 2])),
        num_heads=tuple(config.get("num_heads", [6, 12, 24, 48])),
        num_classes=0,
    )

    return model


class ArkInference(BaseInferenceModel):
    """Ark+ Foundation Model — Swin Transformer Large.

    - 768x768 girdi, ImageNet normalizasyon
    - 14 patoloji tahmini (NIH14, head_n=2)
    - 1376 boyutlu embedding çıkarımı
    - CPU'da ~2-3s/grafi, GPU'da <1s
    """

    _model: Any = None
    _device: str = "cpu"
    _head_n: int = 2  # NIH14 head

    @classmethod
    def load_model(cls, config: dict) -> None:
        """Ark+ modelini ağırlıklarla birlikte yükle.

        Args:
            config: {
                "weights_path": str — checkpoint dosya yolu,
                "device": str — "cpu" veya "cuda",
                "checkpoint_key": str — "teacher" (varsayılan),
                ...model parametreleri...
            }
        """
        import torch

        weights_path = config.get("weights_path")
        if not weights_path or not Path(weights_path).exists():
            raise ModelNotAvailableError(
                "Ark+ Foundation",
                f"Checkpoint bulunamadı: {weights_path}. "
                "Kaggle dataset 'ridvancebec/ark-plus-pretrained-weights-core' gerekli.",
            )

        cls._device = config.get("device", "cpu")
        checkpoint_key = config.get("checkpoint_key", "teacher")
        cls._head_n = config.get("head_n", 2)

        # Model oluştur
        logger.info("Ark+ modeli oluşturuluyor...")
        model = _build_ark_model(config)

        # Checkpoint yükle
        logger.info(f"Checkpoint yükleniyor: {weights_path}")
        checkpoint = torch.load(str(weights_path), map_location="cpu")

        logger.info(f"Checkpoint anahtarları: {list(checkpoint.keys())}")
        state_dict = checkpoint[checkpoint_key]

        # 'module.' ön-ekini kaldır (DDP ile eğitilmiş modellerde olur)
        cleaned = {}
        for k, v in state_dict.items():
            new_key = k.replace("module.", "") if k.startswith("module.") else k
            cleaned[new_key] = v

        load_result = model.load_state_dict(cleaned, strict=False)
        logger.info(
            f"Ağırlık yükleme: eksik={len(load_result.missing_keys)}, "
            f"beklenmeyen={len(load_result.unexpected_keys)}"
        )

        model = model.to(cls._device)
        model.eval()

        n_params = sum(p.numel() for p in model.parameters())
        logger.info(
            f"Ark+ yüklendi: {n_params / 1e6:.1f}M parametre, device={cls._device}"
        )

        cls._model = model

    @classmethod
    def predict(cls, image: "np.ndarray | torch.Tensor") -> dict:
        """Ark+ ile 14 patoloji tespiti.

        Args:
            image: Önceden işlenmiş tensor (1, 3, 768, 768) — ImageNet normalize
                   veya (B, 3, 768, 768) batch

        Returns:
            {
                "predictions": {"Atelectasis": 0.12, "Nodule": 0.72, ...},
                "embedding": np.ndarray(1376,),
                "raw_scores": np.ndarray(14,),
            }
        """
        import torch

        if not cls.is_loaded():
            raise ModelNotAvailableError(
                "Ark+ Foundation", "Model yüklü değil. load_model() çağrılmalı."
            )

        if isinstance(image, np.ndarray):
            image = torch.from_numpy(image).float()
        image = image.to(cls._device)

        with torch.no_grad():
            with torch.amp.autocast(device_type=cls._device.split(":")[0] if ":" in cls._device else cls._device, enabled=cls._device != "cpu"):
                embedding, logits = cls._model(image, head_n=cls._head_n)

        probs = torch.sigmoid(logits).cpu().numpy()
        embedding_np = embedding.cpu().float().numpy()

        # İlk batch elemanının sonuçlarını döndür
        if probs.ndim == 2:
            probs = probs[0]
            embedding_np = embedding_np[0]

        predictions = {}
        for i, label in enumerate(NIH14_LABELS):
            if i < len(probs):
                predictions[label] = round(float(probs[i]), 4)

        return {
            "predictions": predictions,
            "embedding": embedding_np,
            "raw_scores": probs,
        }

    @classmethod
    def extract_embeddings(cls, image: "np.ndarray | torch.Tensor") -> np.ndarray:
        """1376 boyutlu embedding çıkar (UMAP/t-SNE/downstream task için).

        Args:
            image: (B, 3, 768, 768) tensor

        Returns:
            (B, 1376) numpy array
        """
        import torch

        if not cls.is_loaded():
            raise ModelNotAvailableError(
                "Ark+ Foundation", "Model yüklü değil."
            )

        if isinstance(image, np.ndarray):
            image = torch.from_numpy(image).float()
        image = image.to(cls._device)

        with torch.no_grad():
            embeddings = cls._model.generate_embeddings(image, after_proj=True)

        return embeddings.cpu().float().numpy()
