#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "=== DANIEL UK RVC DEPENDENCIES ==="

pkg install -y \
  ffmpeg \
  libsndfile \
  libopenblas \
  clang \
  cmake \
  pkg-config \
  python-torchaudio

echo "[1/3] Installing audio libraries..."

python -m pip install \
  --no-deps \
  soundfile \
  librosa

echo "[2/3] Installing supporting libraries..."

python -m pip install \
  --no-deps \
  audioread \
  soxr \
  lazy_loader \
  msgpack \
  pooch \
  decorator \
  joblib \
  threadpoolctl

echo "[3/3] Checking imports..."

python - <<'PY'
import importlib

for name in [
    "torch",
    "torchaudio",
    "soundfile",
    "librosa",
    "scipy",
    "numpy",
]:
    try:
        module = importlib.import_module(name)
        print(f"[OK] {name}: {getattr(module, '__version__', 'installed')}")
    except Exception as exc:
        print(f"[FAIL] {name}: {exc}")
PY

echo
echo "Dependency installation completed."
