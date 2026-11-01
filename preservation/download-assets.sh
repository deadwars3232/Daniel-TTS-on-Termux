#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

BASE="$HOME/daniel_voice/rvc-source"
ASSETS="$BASE/assets"

mkdir -p "$ASSETS/hubert"
mkdir -p "$ASSETS/rmvpe"

echo "=== DOWNLOADING RVC MODELS ==="

echo
echo "[1/2] Downloading HuBERT..."

curl -fL --retry 3 \
  "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt" \
  -o "$ASSETS/hubert/hubert_base.pt.part"

mv "$ASSETS/hubert/hubert_base.pt.part" \
   "$ASSETS/hubert/hubert_base.pt"

echo
echo "[2/2] Downloading RMVPE..."

curl -fL --retry 3 \
  "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt" \
  -o "$ASSETS/rmvpe/rmvpe.pt.part"

mv "$ASSETS/rmvpe/rmvpe.pt.part" \
   "$ASSETS/rmvpe/rmvpe.pt"

echo
echo "=== VERIFYING DOWNLOADS ==="

ls -lh \
  "$ASSETS/hubert/hubert_base.pt" \
  "$ASSETS/rmvpe/rmvpe.pt"

echo
echo "=== DOWNLOAD COMPLETE ==="
