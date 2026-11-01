#!/data/data/com.termux/files/usr/bin/bash
set -e

cd "$HOME/daniel_voice"

echo "=== DANIEL UK RVC SETUP ==="

pkg install -y git

if [ ! -d rvc-source ]; then
    git clone --depth 1 \
      https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git \
      rvc-source
fi

echo
echo "[1] Checking RVC inference files..."

find rvc-source -type f \
  \( -name 'infer.py' \
  -o -name 'pipeline.py' \
  -o -name 'models.py' \
  -o -name 'config.py' \) | head -30

echo
echo "[2] Checking model files..."

ls -lh \
  DanielUK_200e.pth \
  trained_IVF343_Flat_nprobe_1_DanielUK_200e_v2.index

echo
echo "[3] Checking additional dependencies..."

python - <<'PY'
import importlib.util

for name in [
    "faiss",
    "transformers",
    "fairseq",
    "torchcrepe",
    "pyworld",
]:
    found = importlib.util.find_spec(name) is not None
    print(f"{name:15} {'OK' if found else 'MISSING'}")
PY

echo
echo "=== SOURCE DOWNLOAD COMPLETE ==="
