"""NB07 + NB13 — CT nodül karakterizasyonu ve malignite skorlaması.

İki model birlikte çalışır:
  NB07  ResNet-50 + CBAM  → suspicious (binary) + risk_class (4-class)
  NB13  EfficientNet-B0 + Tabular  → malignity_score (binary) + malignancy_class (5-class)

NB13 birincil malignite referansı; NB07 destekleyici risk sınıfı verir.
Her ikisi de Lung-RADS kategorisi üretir.

Model dosyaları:
  ml/weights/nb07_ct_char/ct_char_best_model.pth   (92 MB)
  ml/weights/nb13_malignancy/malignancy_best_model.pth (17 MB)
  ml/evaluation/nb13_pipeline_config.json  (scaler mean/scale)
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np

from ml.inference.base import BaseInferenceModel, ModelNotAvailableError

logger = logging.getLogger(__name__)

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
PATCH_SIZE = 128

# NB07 risk sınıf isimleri
NB07_RISK_CLASSES = ["Düşük Risk", "Orta-Düşük", "Orta-Yüksek", "Yüksek Risk"]
NB07_LUNG_RADS = ["1", "2", "3", "4A"]

# NB13 malignite sınıf isimleri
NB13_CLASSES = ["Kesinlikle Benign", "Muhtemelen Benign", "Belirsiz",
                "Muhtemelen Malign", "Kesinlikle Malign"]
NB13_LUNG_RADS = ["1", "2", "3", "4A", "4B"]


def _weights_dir() -> Path:
    return Path(os.environ.get(
        "ALPCAN_WEIGHTS_DIR",
        Path(__file__).parents[2] / "ml" / "weights"
    ))


def _nb07_weights() -> Path:
    return _weights_dir() / "nb07_ct_char" / "ct_char_best_model.pth"


def _nb13_weights() -> Path:
    return _weights_dir() / "nb13_malignancy" / "malignancy_best_model.pth"


def _nb13_config() -> Path:
    return Path(__file__).parents[2] / "ml" / "evaluation" / "nb13_pipeline_config.json"


# ─── Model tanımları (NB07) ────────────────────────────────────────────────────

def _build_nb07_model():
    import torch.nn as nn
    from torchvision import models

    class ChannelAttention(nn.Module):
        def __init__(self, channels, reduction=16):
            super().__init__()
            self.avg_pool = nn.AdaptiveAvgPool2d(1)
            self.max_pool = nn.AdaptiveMaxPool2d(1)
            self.fc = nn.Sequential(
                nn.Linear(channels, channels // reduction, bias=False),
                nn.ReLU(inplace=True),
                nn.Linear(channels // reduction, channels, bias=False),
            )
        def forward(self, x):
            b, c = x.size()[:2]
            avg = self.fc(self.avg_pool(x).view(b, c))
            mx  = self.fc(self.max_pool(x).view(b, c))
            return x * nn.functional.sigmoid(avg + mx).view(b, c, 1, 1)

    class SpatialAttention(nn.Module):
        def __init__(self, kernel_size=7):
            super().__init__()
            self.conv = nn.Conv2d(2, 1, kernel_size, padding=kernel_size // 2, bias=False)
        def forward(self, x):
            avg = torch.mean(x, dim=1, keepdim=True)
            mx, _ = torch.max(x, dim=1, keepdim=True)
            return x * torch.sigmoid(self.conv(torch.cat([avg, mx], dim=1)))

    class CBAM(nn.Module):
        def __init__(self, channels):
            super().__init__()
            self.ch = ChannelAttention(channels)
            self.sp = SpatialAttention()
        def forward(self, x):
            return self.sp(self.ch(x))

    class ResNet50CBAM(nn.Module):
        def __init__(self):
            super().__init__()
            resnet = models.resnet50(weights=None)
            self.features = nn.Sequential(*list(resnet.children())[:-2])
            self.cbam = CBAM(2048)
            self.gap = nn.AdaptiveAvgPool2d(1)
            self.dropout = nn.Dropout(0.3)
            self.fc_suspicious = nn.Linear(2048, 1)
            self.fc_risk = nn.Linear(2048, 4)
        def forward(self, x):
            f = self.cbam(self.features(x))
            p = self.dropout(self.gap(f).flatten(1))
            return self.fc_suspicious(p).squeeze(-1), self.fc_risk(p), f

    import torch
    return ResNet50CBAM()


# ─── Model tanımları (NB13) ────────────────────────────────────────────────────

def _build_nb13_model(n_tabular: int = 19):
    import torch.nn as nn
    from torchvision import models

    class MalignancyNet(nn.Module):
        def __init__(self, n_tabular_features):
            super().__init__()
            effnet = models.efficientnet_b0(weights=None)
            self.image_features = effnet.features
            self.image_pool = nn.AdaptiveAvgPool2d(1)
            self.tabular_branch = nn.Sequential(
                nn.Linear(n_tabular_features, 128),
                nn.BatchNorm1d(128),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(128, 128),
                nn.ReLU(),
            )
            self.classifier = nn.Sequential(
                nn.Dropout(0.4),
                nn.Linear(1280 + 128, 256),
                nn.BatchNorm1d(256),
                nn.ReLU(),
                nn.Dropout(0.3),
            )
            self.fc_binary = nn.Linear(256, 1)
            self.fc_malignancy = nn.Linear(256, 5)

        def forward(self, image, tabular):
            img = self.image_pool(self.image_features(image)).flatten(1)
            tab = self.tabular_branch(tabular)
            fused = self.classifier(torch.cat([img, tab], dim=1))
            return self.fc_binary(fused).squeeze(-1), self.fc_malignancy(fused)

    import torch
    return MalignancyNet(n_tabular)


# ─── Tabular özellik hesaplama ─────────────────────────────────────────────────

def _compute_tabular_features(patch_hu: np.ndarray,
                               mask: Optional[np.ndarray] = None,
                               n_slices: int = 1) -> np.ndarray:
    """2D nodül patch'inden 19 radiomic özellik hesapla.

    patch_hu : (H, W) HU değerleri
    mask     : (H, W) binary nodül maskesi (None ise eşikle üret)
    n_slices : 3D segmentasyondan gelen slice sayısı
    """
    from scipy.ndimage import sobel, binary_dilation
    from skimage.measure import regionprops, label
    from skimage.feature import graycomatrix, graycoprops

    if mask is None:
        threshold = patch_hu.mean()
        mask = (patch_hu > threshold).astype(np.uint8)

    mask_bool = mask.astype(bool)
    area = float(mask_bool.sum())
    if area < 1:
        area = 1.0

    # ─ Şekil özellikleri ───────────────────────────────────────────────────────
    labeled = label(mask_bool)
    props_list = regionprops(labeled)
    if props_list:
        props = max(props_list, key=lambda p: p.area)
        eccentricity = float(props.eccentricity)
        solidity = float(props.solidity)
        perimeter = float(props.perimeter) if props.perimeter > 0 else 1.0
        compactness = float(4 * np.pi * area / (perimeter ** 2))
    else:
        eccentricity = 0.0
        solidity = 1.0
        perimeter = float(2 * np.pi * np.sqrt(area / np.pi))
        compactness = 1.0

    diameter_px = float(2 * np.sqrt(area / np.pi))

    # ─ Kenar keskinliği ────────────────────────────────────────────────────────
    sx = sobel(mask_bool.astype(float), axis=0)
    sy = sobel(mask_bool.astype(float), axis=1)
    border_mask = (np.sqrt(sx**2 + sy**2) > 0.1)
    if border_mask.sum() > 0:
        margin_sharpness = float(np.abs(patch_hu[border_mask]).mean())
    else:
        margin_sharpness = 0.0

    # ─ Yoğunluk istatistikleri ────────────────────────────────────────────────
    nodule_pixels = patch_hu[mask_bool]
    intensity_mean = float(nodule_pixels.mean()) if len(nodule_pixels) > 0 else 0.0
    intensity_std  = float(nodule_pixels.std())  if len(nodule_pixels) > 0 else 0.0

    # Çevre doku (dilate − mask)
    surround = binary_dilation(mask_bool, iterations=5) & ~mask_bool
    surround_pixels = patch_hu[surround]
    surround_mean = float(surround_pixels.mean()) if len(surround_pixels) > 0 else 0.0
    surround_std  = float(surround_pixels.std())  if len(surround_pixels) > 0 else 0.0
    contrast_ratio = float(intensity_mean / surround_mean) if surround_mean != 0 else 1.0

    # ─ GLCM doku özellikleri ──────────────────────────────────────────────────
    try:
        # Normalize HU → [0, 255]
        patch_norm = np.clip(patch_hu, -1000, 400)
        patch_uint8 = ((patch_norm + 1000) / 1400 * 255).astype(np.uint8)
        patch_roi = patch_uint8[mask_bool.any(axis=1)][:, mask_bool.any(axis=0)]
        if patch_roi.size < 4:
            raise ValueError("patch too small")
        glcm = graycomatrix(patch_roi, distances=[1], angles=[0],
                            levels=256, symmetric=True, normed=True)
        glcm_homogeneity = float(graycoprops(glcm, "homogeneity")[0, 0])
        glcm_contrast    = float(graycoprops(glcm, "contrast")[0, 0])
        glcm_energy      = float(graycoprops(glcm, "energy")[0, 0])
        glcm_correlation = float(graycoprops(glcm, "correlation")[0, 0])
    except Exception:
        glcm_homogeneity = 0.5
        glcm_contrast    = 100.0
        glcm_energy      = 0.1
        glcm_correlation = 0.5

    # ─ Annotasyon meta (real inference defaults) ──────────────────────────────
    n_annotators = 1
    annotator_area_std = 0.0

    features = np.array([
        diameter_px, area, compactness, eccentricity, solidity, perimeter,
        margin_sharpness, intensity_mean, intensity_std,
        surround_mean, surround_std, contrast_ratio,
        glcm_homogeneity, glcm_contrast, glcm_energy, glcm_correlation,
        n_annotators, float(n_slices), annotator_area_std,
    ], dtype=np.float32)

    return features


def _lu_rads_from_diameter(diameter_px: float, px_spacing_mm: float = 0.7) -> str:
    """Çap (mm) → Lung-RADS kategori (fallback)."""
    diam_mm = diameter_px * px_spacing_mm
    if diam_mm < 6:
        return "1"
    elif diam_mm < 8:
        return "2"
    elif diam_mm < 15:
        return "3"
    else:
        return "4A"


# ─── Ana inference sınıfı ─────────────────────────────────────────────────────

class CharacterizationInference(BaseInferenceModel):
    """NB07 ResNet-50+CBAM + NB13 EfficientNet-B0+Tabular karakterizasyon."""

    _model_nb07 = None
    _model_nb13 = None
    _scaler_mean: Optional[np.ndarray] = None
    _scaler_scale: Optional[np.ndarray] = None
    _device: str = "cpu"

    @classmethod
    def load_model(cls, config: dict) -> None:
        import torch

        cls._device = "cuda" if torch.cuda.is_available() else "cpu"
        errors = []

        # NB07
        nb07_path = _nb07_weights()
        if nb07_path.exists():
            try:
                m = _build_nb07_model()
                ckpt = torch.load(nb07_path, map_location=cls._device)
                m.load_state_dict(ckpt.get("model_state_dict", ckpt))
                m.eval().to(cls._device)
                cls._model_nb07 = m
                logger.info(f"NB07 ResNet50+CBAM yüklendi — {cls._device}")
            except Exception as e:
                errors.append(f"NB07: {e}")
        else:
            errors.append(f"NB07 ağırlığı yok: {nb07_path}")

        # NB13
        nb13_path = _nb13_weights()
        if nb13_path.exists():
            try:
                m = _build_nb13_model(n_tabular=19)
                ckpt = torch.load(nb13_path, map_location=cls._device)
                m.load_state_dict(ckpt.get("model_state_dict", ckpt))
                m.eval().to(cls._device)
                cls._model_nb13 = m
                # Scaler parametrelerini yükle
                cfg_path = _nb13_config()
                if cfg_path.exists():
                    with open(cfg_path) as f:
                        cfg = json.load(f)
                    sc = cfg.get("scaler", {})
                    cls._scaler_mean  = np.array(sc.get("mean", [0] * 19), dtype=np.float32)
                    cls._scaler_scale = np.array(sc.get("scale", [1] * 19), dtype=np.float32)
                logger.info(f"NB13 EfficientNet+Tabular yüklendi — {cls._device}")
            except Exception as e:
                errors.append(f"NB13: {e}")
        else:
            errors.append(f"NB13 ağırlığı yok: {nb13_path}")

        if cls._model_nb07 is None and cls._model_nb13 is None:
            raise ModelNotAvailableError(
                "Karakterizasyon",
                "Her iki model de yüklenemedi: " + "; ".join(errors)
            )
        if errors:
            logger.warning("Kısmi yükleme: " + "; ".join(errors))

    @classmethod
    def predict(
        cls,
        patch_hu: np.ndarray,
        mask: Optional[np.ndarray] = None,
        n_slices: int = 1,
        px_spacing_mm: float = 0.7,
    ) -> dict:
        """Tek nodül patch'ini karakterize et.

        Args:
            patch_hu    : (H, W) HU değerleri — nodül etrafında kırpılmış
            mask        : (H, W) binary nodül maskesi (opsiyonel)
            n_slices    : 3D analizde kaç slice kapsıyor
            px_spacing_mm: piksel boyutu mm cinsinden

        Returns:
            {
                "malignancy_score":   float 0-1   (NB13 birincil)
                "malignancy_class":   str          (NB13 5-class adı)
                "lung_rads":          str          ("1"/"2"/"3"/"4A"/"4B")
                "risk_class":         str          (NB07 4-class adı)
                "suspicious":         bool
                "confidence":         float 0-1
                "diameter_mm":        float
            }
        """
        import torch
        import torch.nn.functional as F
        import cv2

        if not cls.is_loaded():
            cls.load_model({})

        # ── Patch ön işleme ─────────────────────────────────────────────────────
        # HU [-1000,400] → [0,1] (soft tissue window)
        p = patch_hu.astype(np.float32)
        p = (np.clip(p, -1000, 400) + 1000) / 1400
        rgb = np.stack([p, p, p], axis=-1)
        rgb = cv2.resize(rgb, (PATCH_SIZE, PATCH_SIZE))
        rgb = (rgb - IMAGENET_MEAN) / IMAGENET_STD
        img_tensor = torch.from_numpy(rgb.transpose(2, 0, 1)).unsqueeze(0).float().to(cls._device)

        # ── 19 tabular özellik ──────────────────────────────────────────────────
        tab_raw = _compute_tabular_features(patch_hu, mask=mask, n_slices=n_slices)
        if cls._scaler_mean is not None:
            tab_norm = (tab_raw - cls._scaler_mean) / np.maximum(cls._scaler_scale, 1e-6)
        else:
            tab_norm = tab_raw
        tab_tensor = torch.from_numpy(tab_norm).unsqueeze(0).float().to(cls._device)
        diameter_mm = float(tab_raw[0]) * px_spacing_mm

        result: dict = {}

        with torch.no_grad():
            # ── NB13 (birincil) ─────────────────────────────────────────────────
            if cls._model_nb13 is not None:
                bin_logit, cls_logit = cls._model_nb13(img_tensor, tab_tensor)
                mal_score = float(torch.sigmoid(bin_logit).cpu().item())
                cls_probs = F.softmax(cls_logit, dim=1).cpu().numpy()[0]
                cls_idx = int(cls_probs.argmax())
                result["malignancy_score"]  = mal_score
                result["malignancy_class"]  = NB13_CLASSES[cls_idx]
                result["malignancy_probs"]  = cls_probs.tolist()
                result["lung_rads"]         = NB13_LUNG_RADS[cls_idx]
                result["suspicious"]        = mal_score >= 0.5
                result["confidence"]        = float(cls_probs[cls_idx])

            # ── NB07 (destekleyici) ──────────────────────────────────────────────
            if cls._model_nb07 is not None:
                susp_logit, risk_logit, _ = cls._model_nb07(img_tensor)
                susp_score = float(torch.sigmoid(susp_logit).cpu().item())
                risk_idx = int(risk_logit.argmax(dim=1).cpu().item())
                result["nb07_suspicious_score"] = susp_score
                result["risk_class"]            = NB07_RISK_CLASSES[risk_idx]
                result["nb07_lung_rads"]        = NB07_LUNG_RADS[risk_idx]
                # NB13 yoksa NB07'yi birincil yap
                if "malignancy_score" not in result:
                    result["malignancy_score"] = susp_score
                    result["lung_rads"]        = NB07_LUNG_RADS[risk_idx]
                    result["suspicious"]       = susp_score >= 0.5
                    result["confidence"]       = susp_score
                    result["malignancy_class"] = NB07_RISK_CLASSES[risk_idx]

        result["diameter_mm"] = diameter_mm
        return result

    @classmethod
    def predict_nodule_list(
        cls,
        volume: np.ndarray,
        nodules: list,
        px_spacing_mm: float = 0.7,
        patch_size: int = PATCH_SIZE,
    ) -> list:
        """Tespit edilen tüm nodülleri karakterize et.

        Args:
            volume  : (D, H, W) HU değerli 3D volume
            nodules : NoduleDetectionInference.predict() çıktısındaki liste
            px_spacing_mm: piksel aralığı mm cinsinden

        Returns:
            Her nodül için karakterizasyon dict'ini içeren liste
        """
        if not cls.is_loaded():
            cls.load_model({})

        D, H, W = volume.shape
        half = patch_size // 2
        results = []

        for nod in nodules:
            z = nod.get("slice_idx", D // 2)
            cy = int(nod.get("center_y", H // 2))
            cx = int(nod.get("center_x", W // 2))

            # Patch sınırlarını hesapla
            y0, y1 = max(0, cy - half), min(H, cy + half)
            x0, x1 = max(0, cx - half), min(W, cx + half)
            patch = volume[z, y0:y1, x0:x1]

            # Mask (NoduleDetectionInference'dan gelen)
            mask_resized = nod.get("mask_resized")
            patch_mask = None
            if mask_resized is not None:
                import cv2
                ph, pw = patch.shape
                patch_mask = cv2.resize(
                    mask_resized.astype(np.uint8), (pw, ph),
                    interpolation=cv2.INTER_NEAREST
                ).astype(bool)

            char = cls.predict(
                patch_hu=patch,
                mask=patch_mask,
                n_slices=nod.get("n_slices", 1),
                px_spacing_mm=px_spacing_mm,
            )
            char["nodule_idx"]  = nodules.index(nod)
            char["center"]      = [cx, cy, z]
            char["diameter_px"] = nod.get("diameter_px")
            results.append(char)

        return results
