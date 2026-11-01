#!/data/data/com.termux/files/usr/bin/bash

set -u

echo "=== FIXING RVC DEPENDENCIES ==="

echo
echo "[1/4] Installing Termux audio libraries..."

pkg install -y \
  ffmpeg \
  libsndfile \
  libopenblas \
  python-numpy \
  python-scipy

echo
echo "[2/4] Installing Python dependencies..."

for package in \
  soundfile \
  audioread \
  lazy_loader \
  msgpack \
  pooch \
  decorator \
  joblib \
  threadpoolctl
do
  echo "Installing $package..."
  python -m pip install --no-deps "$package" || \
    echo "WARNING: $package installation failed"
done

echo
echo "[3/4] Installing librosa without soxr..."

python -m pip install --no-deps librosa || \
  echo "WARNING: librosa installation failed"

echo
echo "[4/4] Testing imports..."

python - <<'PY'
import importlib

packages = [
    "torch",
    "numpy",
    "scipy",
    "soundfile",
    "librosa",
    "torchaudio",
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
echo "=== FINISHED ==="
