#!/bin/bash
# AlpCAN — Kaggle Notebook Output Sync Script
# Kaggle'da çalıştırılan notebook çıktılarını indirir ve GitHub'a kaydeder.
# Kullanım: ./kaggle_sync.sh [notebook_slug]
# Örnek: ./kaggle_sync.sh ridvancebec/alpcan-lidc-idri-exploration

set -e

KAGGLE_USER="ridvancebec"
NOTEBOOKS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUTS_DIR="$NOTEBOOKS_DIR/outputs"

# Tüm AlpCAN notebook'larını senkronize et
sync_notebook() {
    local slug="$1"
    local kernel_name="${slug##*/}"
    local output_dir="$OUTPUTS_DIR/$kernel_name"

    echo "📥 Syncing: $slug"

    # Durumu kontrol et
    status=$(kaggle kernels status "$slug" 2>&1 | tail -1)
    echo "   Status: $status"

    if echo "$status" | grep -q "complete"; then
        mkdir -p "$output_dir"
        kaggle kernels output "$slug" -p "$output_dir"
        echo "   ✅ Output saved to: $output_dir"
    else
        echo "   ⏳ Notebook not complete yet, skipping..."
    fi
}

if [ -n "$1" ]; then
    # Tek notebook sync
    sync_notebook "$1"
else
    # Tüm bilinen notebook'ları sync
    echo "🔄 AlpCAN Kaggle Notebook Sync"
    echo "================================"

    sync_notebook "$KAGGLE_USER/alpcan-lidc-idri-exploration"
    # Yeni notebook'lar eklendikçe buraya ekle:
    # sync_notebook "$KAGGLE_USER/alpcan-cxr-ensemble"
    # sync_notebook "$KAGGLE_USER/alpcan-nnunet-training"

    echo ""
    echo "================================"
    echo "✅ Sync complete!"
    echo "💡 Don't forget: git add notebooks/outputs/ && git commit && git push"
fi
