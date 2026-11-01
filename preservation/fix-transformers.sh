#!/data/data/com.termux/files/usr/bin/bash

set -u

cd "$HOME/daniel_voice"

echo "=================================="
echo " DANIEL UK RVC DEPENDENCY REPAIR"
echo "=================================="

echo
echo "[1/3] Installing Transformers dependencies..."

for package in \
    huggingface-hub \
    packaging \
    pyyaml \
    regex \
    tokenizers \
    safetensors \
    tqdm \
    requests \
    typer
do
    echo
    echo "Installing: $package"

    python -m pip install --no-deps "$package" ||
        echo "[WARNING] Could not install $package"
done

echo
echo "[2/3] Checking Python packages..."

python - <<'PY'
import importlib

packages = [
    "torch",
    "torchaudio",
    "numpy",
    "scipy",
    "soundfile",
    "librosa",
    "transformers",
    "huggingface_hub",
    "tokenizers",
    "safetensors",
]

for name in packages:
    try:
        module = importlib.import_module(name)
        version = getattr(module, "__version__", "installed")
        print(f"[OK] {name}: {version}")
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
PY

echo
echo "[3/3] Checking package compatibility..."

python -m pip check || true

echo
echo "=================================="
echo " DIAGNOSTICS COMPLETE"
echo "=================================="
