#!/usr/bin/env bash
# AlpCAN — Model ağırlıklarını sunucuya yükle
# Usage: bash deploy/upload-weights.sh
# NOT: Proje kökünden çalıştırılmalı
#
# deploy-remote.sh tarafından dışlanan .pth dosyaları bu script ile sunucuya aktarılır.
# Sunucuda ml/ dizini container'a /app/ml olarak mount edildiğinden
# ağırlıklar otomatik olarak Celery worker tarafından kullanılır.

set -euo pipefail

if [ -z "${SERVER_IP:-}" ] || [ -z "${SERVER_USER:-}" ]; then
    echo "HATA: SERVER_IP ve SERVER_USER env değişkenleri tanımlı olmalı."
    echo "  export SERVER_IP=x.x.x.x"
    echo "  export SERVER_USER=kullanici"
    exit 1
fi

DEPLOY_PATH="${DEPLOY_PATH:-/root/alpcan}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SSH="ssh -i $SSH_KEY"
SCP="scp -i $SSH_KEY"
REMOTE="$SERVER_USER@$SERVER_IP"

echo "======================================"
echo "AlpCAN Model Ağırlıkları Yükleme"
echo "======================================"
echo "Server: $REMOTE"
echo "Hedef:  $DEPLOY_PATH/ml/weights/"
echo ""

# Uzak dizinleri oluştur
$SSH "$REMOTE" "
    mkdir -p $DEPLOY_PATH/ml/weights/nb06_ct_seg
    mkdir -p $DEPLOY_PATH/ml/weights/nb07_ct_char
    mkdir -p $DEPLOY_PATH/ml/weights/nb13_malignancy
    mkdir -p $DEPLOY_PATH/ml/weights/nb12_lora
    mkdir -p $DEPLOY_PATH/ml/evaluation
"

upload_if_exists() {
    local local_path="$1"
    local remote_path="$2"
    local label="$3"

    if [ -f "$local_path" ]; then
        local size
        size=$(du -h "$local_path" | cut -f1)
        echo "  Yükleniyor: $label ($size)..."
        $SCP "$local_path" "$REMOTE:$remote_path"
        echo "  [✓] $label"
    else
        echo "  [—] $label — yerel dosya bulunamadı, atlandı"
    fi
}

echo "--- CT Segmentasyon (NB06) ---"
upload_if_exists \
    "$PROJECT_ROOT/ml/weights/nb06_ct_seg/ct_seg_best_model.pth" \
    "$DEPLOY_PATH/ml/weights/nb06_ct_seg/ct_seg_best_model.pth" \
    "NB06 U-Net ResNet-34 (ct_seg_best_model.pth)"

echo ""
echo "--- CT Nodül Karakterizasyon (NB07) ---"
upload_if_exists \
    "$PROJECT_ROOT/ml/weights/nb07_ct_char/ct_char_best_model.pth" \
    "$DEPLOY_PATH/ml/weights/nb07_ct_char/ct_char_best_model.pth" \
    "NB07 ResNet-50+CBAM (ct_char_best_model.pth)"

echo ""
echo "--- Malignite Skoru (NB13) ---"
upload_if_exists \
    "$PROJECT_ROOT/ml/weights/nb13_malignancy/malignancy_best_model.pth" \
    "$DEPLOY_PATH/ml/weights/nb13_malignancy/malignancy_best_model.pth" \
    "NB13 EfficientNet-B0+Tabular (malignancy_best_model.pth)"

echo ""
echo "--- NB13 Pipeline Config (Scaler) ---"
upload_if_exists \
    "$PROJECT_ROOT/ml/evaluation/nb13_pipeline_config.json" \
    "$DEPLOY_PATH/ml/evaluation/nb13_pipeline_config.json" \
    "NB13 StandardScaler parametreleri (nb13_pipeline_config.json)"

echo ""
echo "--- NB12 LoRA Adaptörü (varsa) ---"
NB12_ADAPTER="$PROJECT_ROOT/ml/weights/nb12_lora/adapter_model.safetensors"
if [ -f "$NB12_ADAPTER" ]; then
    upload_if_exists \
        "$NB12_ADAPTER" \
        "$DEPLOY_PATH/ml/weights/nb12_lora/adapter_model.safetensors" \
        "NB12 LoRA adapter_model.safetensors"
    # Config dosyaları
    for f in adapter_config.json tokenizer.json tokenizer_config.json chat_template.jinja; do
        upload_if_exists \
            "$PROJECT_ROOT/ml/weights/nb12_lora/$f" \
            "$DEPLOY_PATH/ml/weights/nb12_lora/$f" \
            "NB12 $f"
    done
else
    echo "  [—] NB12 LoRA — adapter_model.safetensors yok, atlandı"
fi

echo ""
echo "--- Uzak durum ---"
$SSH "$REMOTE" "
    echo 'Sunucudaki model ağırlıkları:'
    find $DEPLOY_PATH/ml/weights -name '*.pth' -o -name '*.safetensors' 2>/dev/null | while read f; do
        echo \"  \$(du -h \$f | cut -f1)  \$f\"
    done
    echo ''
    echo 'Scaler config:'
    ls -lh $DEPLOY_PATH/ml/evaluation/*.json 2>/dev/null || echo '  (yok)'
"

echo ""
echo "======================================"
echo "Ağırlık yükleme tamamlandı!"
echo "Celery worker container'ı yeniden başlatmak için:"
echo "  ssh $REMOTE 'cd $DEPLOY_PATH && docker compose -f docker-compose.prod.yml restart celery'"
echo "======================================"
