"""Lung-RADS 2022 v1.1 kategori atama mantığı.

Nodül boyutu, yoğunluk, büyüme oranına göre Lung-RADS kategorisi belirler.
ACR Lung-RADS v2022 kılavuzuna uygun.
"""

from dataclasses import dataclass


@dataclass
class NoduleInfo:
    """Nodül bilgisi — Lung-RADS skoru hesaplamak için gereken minimum veri."""

    diameter_mm: float
    density: str  # "solid", "part_solid", "ground_glass"
    volume_mm3: float | None = None
    volume_doubling_time_days: float | None = None  # VDT
    solid_component_mm: float | None = None  # Part-solid nodüllerde katı kısım
    is_new: bool = False
    is_growing: bool = False
    is_perifissural: bool = False  # Perifissüral → muhtemelen lenf nodu


def classify_lung_rads(nodule: NoduleInfo) -> str:
    """Nodül özelliklerine göre Lung-RADS 2022 kategorisi ata.

    Returns:
        Lung-RADS kategorisi: "1", "2", "3", "4A", "4B", "4X"
    """
    d = nodule.diameter_mm
    density = nodule.density.lower()

    # Perifissüral nodüller (muhtemelen lenf nodu) → 2
    if nodule.is_perifissural and d < 10:
        return "2"

    # Solid nodüller
    if density == "solid":
        return _classify_solid(nodule)

    # Part-solid nodüller
    if density in ("part_solid", "part-solid", "mixed"):
        return _classify_part_solid(nodule)

    # Ground-glass (saf buzlu cam) nodüller
    if density in ("ground_glass", "ground-glass", "ggo", "ggn"):
        return _classify_ground_glass(nodule)

    # Bilinmeyen yoğunluk → solid olarak değerlendir
    return _classify_solid(nodule)


def _classify_solid(nodule: NoduleInfo) -> str:
    """Solid nodül Lung-RADS sınıflandırması."""
    d = nodule.diameter_mm

    # Yeni ve büyüyen solid nodül
    if nodule.is_new and d >= 4:
        return "4B" if d >= 8 else "4A"

    if d < 6:
        return "2"
    elif d < 8:
        if nodule.is_growing:
            return "4A"
        return "3"
    elif d < 15:
        if nodule.is_growing:
            return "4B"
        return "4A"
    else:
        return "4B"


def _classify_part_solid(nodule: NoduleInfo) -> str:
    """Part-solid nodül Lung-RADS sınıflandırması."""
    d = nodule.diameter_mm
    solid_mm = nodule.solid_component_mm or 0

    if d < 6:
        return "2"

    # Toplam boyut ≥ 6mm
    if solid_mm < 6:
        if nodule.is_growing:
            return "4A"
        return "3"
    elif solid_mm < 8:
        if nodule.is_growing:
            return "4B"
        return "4A"
    else:
        return "4B"


def _classify_ground_glass(nodule: NoduleInfo) -> str:
    """Ground-glass (saf buzlu cam) nodül Lung-RADS sınıflandırması."""
    d = nodule.diameter_mm

    if d < 30:
        if nodule.is_growing:
            return "4A"
        if d < 20:
            return "2"
        return "3"
    else:
        if nodule.is_growing:
            return "4B"
        return "4A"


def classify_overall_lung_rads(nodules: list[NoduleInfo]) -> str:
    """Tüm nodüllerin en yüksek Lung-RADS kategorisini döndür.

    Birden fazla nodül varsa, en riskli kategoriye göre karar verilir.

    Args:
        nodules: Nodül listesi

    Returns:
        Genel Lung-RADS kategorisi
    """
    if not nodules:
        return "1"  # Nodül yok → negatif tarama

    category_order = {"1": 0, "2": 1, "3": 2, "4A": 3, "4B": 4, "4X": 5}

    categories = [classify_lung_rads(n) for n in nodules]
    highest = max(categories, key=lambda c: category_order.get(c, 0))

    return highest


def get_recommendation(lung_rads: str) -> dict:
    """Lung-RADS kategorisine göre takip önerisi döndür.

    Returns:
        {"category": str, "action_tr": str, "follow_up_months": int | None,
         "malignancy_risk": str}
    """
    recommendations = {
        "1": {
            "category": "1",
            "action_tr": "Negatif — nodül yok. Yıllık LDBT taraması ile devam.",
            "follow_up_months": 12,
            "malignancy_risk": "< %1",
        },
        "2": {
            "category": "2",
            "action_tr": "Benign görünüm — muhtemelen zararsız bulgu. Yıllık LDBT taraması ile devam.",
            "follow_up_months": 12,
            "malignancy_risk": "< %1",
        },
        "3": {
            "category": "3",
            "action_tr": "Muhtemelen benign — 6 ay sonra LDBT kontrolü önerilir.",
            "follow_up_months": 6,
            "malignancy_risk": "%1-2",
        },
        "4A": {
            "category": "4A",
            "action_tr": "Şüpheli — 3 ay sonra LDBT kontrolü veya PET/BT önerilir.",
            "follow_up_months": 3,
            "malignancy_risk": "%5-15",
        },
        "4B": {
            "category": "4B",
            "action_tr": "Yüksek şüphe — doku biyopsisi veya cerrahi rezeksiyon düşünülmeli. Göğüs cerrahisi/onkoloji konsültasyonu önerilir.",
            "follow_up_months": None,
            "malignancy_risk": "> %15",
        },
        "4X": {
            "category": "4X",
            "action_tr": "Ek bulgularla yüksek şüphe — ileri tetkik ve multidisipliner değerlendirme gerekli.",
            "follow_up_months": None,
            "malignancy_risk": "> %15",
        },
    }
    return recommendations.get(lung_rads, recommendations["1"])
