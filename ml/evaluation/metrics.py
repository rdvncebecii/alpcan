"""Değerlendirme metrikleri — AUC-ROC, Dice, IoU, hassasiyet/özgüllük."""

import numpy as np


def auc_roc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """ROC eğrisi altındaki alan (AUC-ROC).

    Basit trapezoidal yöntemle hesaplanır. sklearn gerekmez.
    """
    # Sıralama indeksleri (azalan score)
    desc_idx = np.argsort(y_scores)[::-1]
    y_true_sorted = y_true[desc_idx]

    # TPR ve FPR hesapla
    total_pos = np.sum(y_true == 1)
    total_neg = np.sum(y_true == 0)

    if total_pos == 0 or total_neg == 0:
        return 0.0

    tp = 0
    fp = 0
    tpr_list = [0.0]
    fpr_list = [0.0]

    for label in y_true_sorted:
        if label == 1:
            tp += 1
        else:
            fp += 1
        tpr_list.append(tp / total_pos)
        fpr_list.append(fp / total_neg)

    # Trapezoidal integral
    auc = 0.0
    for i in range(1, len(fpr_list)):
        auc += (fpr_list[i] - fpr_list[i - 1]) * (tpr_list[i] + tpr_list[i - 1]) / 2

    return float(auc)


def sensitivity_specificity(
    y_true: np.ndarray, y_pred: np.ndarray
) -> dict:
    """Hassasiyet (sensitivity/recall) ve özgüllük (specificity) hesapla.

    Args:
        y_true: Gerçek etiketler (0/1)
        y_pred: Tahmin etiketleri (0/1)

    Returns:
        {"sensitivity": float, "specificity": float, "ppv": float, "npv": float}
    """
    tp = int(np.sum((y_pred == 1) & (y_true == 1)))
    tn = int(np.sum((y_pred == 0) & (y_true == 0)))
    fp = int(np.sum((y_pred == 1) & (y_true == 0)))
    fn = int(np.sum((y_pred == 0) & (y_true == 1)))

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0.0  # Positive Predictive Value
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0  # Negative Predictive Value

    return {
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
        "ppv": float(ppv),
        "npv": float(npv),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def dice_coefficient(mask_pred: np.ndarray, mask_true: np.ndarray) -> float:
    """Dice benzerlik katsayısı (segmentasyon değerlendirmesi).

    DSC = 2 * |A ∩ B| / (|A| + |B|)
    """
    pred_bool = mask_pred.astype(bool)
    true_bool = mask_true.astype(bool)

    intersection = np.sum(pred_bool & true_bool)
    total = np.sum(pred_bool) + np.sum(true_bool)

    if total == 0:
        return 1.0  # Her iki maske de boş → mükemmel eşleşme

    return float(2.0 * intersection / total)


def iou_score(mask_pred: np.ndarray, mask_true: np.ndarray) -> float:
    """Intersection over Union (Jaccard indeksi).

    IoU = |A ∩ B| / |A ∪ B|
    """
    pred_bool = mask_pred.astype(bool)
    true_bool = mask_true.astype(bool)

    intersection = np.sum(pred_bool & true_bool)
    union = np.sum(pred_bool | true_bool)

    if union == 0:
        return 1.0

    return float(intersection / union)


def froc_score(
    detections: list[dict],
    ground_truth: list[dict],
    distance_threshold_mm: float = 15.0,
) -> dict:
    """Free-Response ROC (FROC) — nodül tespiti değerlendirmesi.

    LUNA16 challenge metriği. Her tespit (x, y, z, confidence) ve
    her ground truth (x, y, z) için eşleşme hesaplar.

    Args:
        detections: [{"center": [x,y,z], "confidence": float}, ...]
        ground_truth: [{"center": [x,y,z]}, ...]
        distance_threshold_mm: Eşleşme mesafe eşiği (mm)

    Returns:
        {"sensitivity_at_fps": dict, "avg_sensitivity": float}
    """
    if not ground_truth:
        return {"sensitivity_at_fps": {}, "avg_sensitivity": 0.0}

    n_gt = len(ground_truth)

    # Confidence'a göre azalan sıra
    sorted_dets = sorted(detections, key=lambda d: d.get("confidence", 0), reverse=True)

    gt_matched = [False] * n_gt
    tp_list = []
    fp_list = []

    for det in sorted_dets:
        det_center = np.array(det["center"])
        matched = False

        for i, gt in enumerate(ground_truth):
            if gt_matched[i]:
                continue
            gt_center = np.array(gt["center"])
            dist = np.linalg.norm(det_center - gt_center)

            if dist <= distance_threshold_mm:
                gt_matched[i] = True
                matched = True
                break

        if matched:
            tp_list.append(1)
            fp_list.append(0)
        else:
            tp_list.append(0)
            fp_list.append(1)

    # Kümülatif TP/FP
    cum_tp = np.cumsum(tp_list)
    cum_fp = np.cumsum(fp_list)

    # LUNA16 FP oranları: 0.125, 0.25, 0.5, 1, 2, 4, 8
    target_fps = [0.125, 0.25, 0.5, 1, 2, 4, 8]
    sensitivity_at_fps = {}

    for target_fp in target_fps:
        # FP sayısının target'ı geçtiği nokta
        idx = np.searchsorted(cum_fp, target_fp, side="right") - 1
        if idx >= 0:
            sensitivity_at_fps[target_fp] = float(cum_tp[idx] / n_gt)
        else:
            sensitivity_at_fps[target_fp] = 0.0

    avg_sensitivity = float(np.mean(list(sensitivity_at_fps.values())))

    return {
        "sensitivity_at_fps": sensitivity_at_fps,
        "avg_sensitivity": avg_sensitivity,
        "total_detections": len(detections),
        "total_ground_truth": n_gt,
    }
