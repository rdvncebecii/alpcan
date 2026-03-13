"""Akciğer segmentasyonu — eşik tabanlı.

BT volümünde akciğer bölgesini maskeleyen basit ama etkili yöntem.
SimpleITK veya deep learning gerektirmez — sadece numpy + scipy.
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def extract_lung_mask(
    volume: np.ndarray,
    threshold_hu: float = -600,
) -> np.ndarray:
    """BT volümünden akciğer maskesi çıkar.

    Algoritma:
    1. HU eşik değeri ile binary maske oluştur
    2. Kenar bağlantılı bileşenleri temizle (vücut + dış hava)
    3. Morfolojik kapanma (delikleri doldur)
    4. En büyük 2 bileşeni tut (sol + sağ akciğer)

    Args:
        volume: 3D numpy array — ham HU değerleri (D, H, W)
        threshold_hu: Akciğer eşik değeri (varsayılan -600 HU)

    Returns:
        Binary maske — aynı boyutta (D, H, W), dtype=bool
    """
    from scipy import ndimage

    logger.info(f"Akciğer maskesi çıkarılıyor: volume={volume.shape}, threshold={threshold_hu}")

    # 1. Binary eşikleme: hava + akciğer bölgesi
    binary = volume < threshold_hu

    # 2. Her dilim için kenar temizliği
    cleaned = np.zeros_like(binary)
    for i in range(binary.shape[0]):
        cleaned[i] = _clear_border_2d(binary[i])

    # 3. Morfolojik kapanma — küçük delikleri doldur
    structure = ndimage.generate_binary_structure(3, 2)
    closed = ndimage.binary_closing(cleaned, structure=structure, iterations=3)

    # 4. Bağlı bileşen analizi — en büyük 2 bileşeni tut
    labeled, num_features = ndimage.label(closed)
    if num_features == 0:
        logger.warning("Akciğer bölgesi bulunamadı")
        return np.zeros_like(volume, dtype=bool)

    # Bileşen boyutlarını hesapla (arka plan=0 hariç)
    component_sizes = ndimage.sum(closed, labeled, range(1, num_features + 1))
    sorted_indices = np.argsort(component_sizes)[::-1]

    # En büyük 2 bileşeni tut (sol + sağ akciğer)
    mask = np.zeros_like(volume, dtype=bool)
    for idx in sorted_indices[:2]:
        mask |= labeled == (idx + 1)

    # 5. Son morfolojik düzeltme
    mask = ndimage.binary_fill_holes(mask)

    lung_volume_pct = mask.sum() / mask.size * 100
    logger.info(f"Akciğer maskesi: {mask.sum()} voxel ({lung_volume_pct:.1f}%)")
    return mask


def _clear_border_2d(binary_slice: np.ndarray) -> np.ndarray:
    """2D dilimde kenar bağlantılı bileşenleri temizle.

    Dış hava ve vücut kenarlarını kaldırır, sadece iç boşlukları (akciğer) tutar.
    """
    from scipy import ndimage

    # Kenar bağlantılı bileşenleri bul
    labeled, num_features = ndimage.label(binary_slice)
    if num_features == 0:
        return binary_slice

    # Kenar piksellerindeki etiketleri bul
    border_labels = set()
    h, w = binary_slice.shape
    border_labels.update(labeled[0, :].flatten())  # üst
    border_labels.update(labeled[-1, :].flatten())  # alt
    border_labels.update(labeled[:, 0].flatten())  # sol
    border_labels.update(labeled[:, -1].flatten())  # sağ
    border_labels.discard(0)  # arka plan

    # Kenar bileşenlerini kaldır
    result = binary_slice.copy()
    for label in border_labels:
        result[labeled == label] = False

    return result
