#!/usr/bin/env bash
# AlpCAN — Model ağırlıkları indirme scripti
# Kullanım: bash ml/weights/download.sh [--all | --ark | --xrv | --medsam]

set -euo pipefail

WEIGHTS_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Ağırlık dizini: $WEIGHTS_DIR"

download_xrv() {
    echo "=== TorchXRayVision DenseNet-121 ==="
    echo "TorchXRayVision ağırlıkları otomatik indirilir (ilk çalıştırmada)."
    echo "Manuel indirmek isterseniz:"
    echo "  python -c \"import torchxrayvision as xrv; xrv.models.DenseNet(weights='densenet121-res224-all')\""
    echo ""
}

download_ark() {
    echo "=== Ark+ Foundation Model ==="
    ARK_DIR="$WEIGHTS_DIR/ark"
    mkdir -p "$ARK_DIR"

    if [ -f "$ARK_DIR/ark_plus_checkpoint.pth" ]; then
        echo "Ark+ ağırlıkları zaten mevcut: $ARK_DIR/ark_plus_checkpoint.pth"
    else
        echo "Ark+ ağırlıkları Kaggle'dan indirilmeli:"
        echo "  1. kaggle.com adresinden 'Ark+ Swin-Large Pretrained Weights' arayın"
        echo "  2. Checkpoint dosyasını indirin"
        echo "  3. $ARK_DIR/ark_plus_checkpoint.pth olarak kaydedin"
        echo ""
        echo "Kaggle CLI ile:"
        echo "  kaggle datasets download -d rdvncebeci/ark-swin-large-pretrained-weights -p $ARK_DIR --unzip"
    fi
    echo ""
}

download_medsam() {
    echo "=== MedSAM (HuggingFace) ==="
    echo "MedSAM ağırlıkları HuggingFace'den otomatik indirilir."
    echo "Manuel önbelleğe almak için:"
    echo "  python -c \"from transformers import SamModel, SamProcessor; SamModel.from_pretrained('flaviagiammarino/medsam-vit-base'); SamProcessor.from_pretrained('flaviagiammarino/medsam-vit-base')\""
    echo ""
}

show_status() {
    echo "=== Model Ağırlıkları Durumu ==="
    echo ""

    # Ark+
    if [ -f "$WEIGHTS_DIR/ark/ark_plus_checkpoint.pth" ]; then
        SIZE=$(du -h "$WEIGHTS_DIR/ark/ark_plus_checkpoint.pth" | cut -f1)
        echo "[✓] Ark+ Foundation Model ($SIZE)"
    else
        echo "[✗] Ark+ Foundation Model — indirilmedi"
    fi

    # TorchXRayVision
    XRV_CACHE="$HOME/.torchxrayvision/models_data"
    if [ -d "$XRV_CACHE" ] && [ "$(ls -A "$XRV_CACHE" 2>/dev/null)" ]; then
        echo "[✓] TorchXRayVision DenseNet-121 (önbellekte)"
    else
        echo "[~] TorchXRayVision — ilk çalıştırmada otomatik indirilecek"
    fi

    # MedSAM
    MEDSAM_CACHE="$HOME/.cache/huggingface/hub/models--flaviagiammarino--medsam-vit-base"
    if [ -d "$MEDSAM_CACHE" ]; then
        echo "[✓] MedSAM ViT-Base (HuggingFace önbellekte)"
    else
        echo "[~] MedSAM — ilk çalıştırmada otomatik indirilecek"
    fi

    # Kullanılamayan modeller
    echo ""
    echo "--- Henüz mevcut olmayan modeller ---"
    echo "[—] X-Raydar: Kod herkese açık değil"
    echo "[—] nnU-Net Nodül Tespiti: Eğitim devam ediyor"
    echo "[—] Nodül Karakterizasyonu: Eğitim devam ediyor"
    echo "[—] Büyüme Takibi: Gelecek fazda eklenecek"
    echo ""
}

case "${1:-status}" in
    --all)
        download_ark
        download_xrv
        download_medsam
        show_status
        ;;
    --ark)
        download_ark
        ;;
    --xrv)
        download_xrv
        ;;
    --medsam)
        download_medsam
        ;;
    --status|status)
        show_status
        ;;
    *)
        echo "Kullanım: $0 [--all | --ark | --xrv | --medsam | --status]"
        exit 1
        ;;
esac
