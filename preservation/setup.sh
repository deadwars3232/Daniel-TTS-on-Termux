#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/daniel_voice"

echo "================================="
echo " DANIEL UK RVC - TERMUX SETUP"
echo "================================="

echo
echo "[1/4] Checking PyTorch..."

python - <<'PY'
import torch
print("PyTorch:", torch.__version__)
print("CPU inference:", "available")
PY

echo
echo "[2/4] Checking model files..."

test -s DanielUK_200e.pth || {
    echo "ERROR: Daniel UK model missing"
    exit 1
}

test -s trained_IVF343_Flat_nprobe_1_DanielUK_200e_v2.index || {
    echo "ERROR: RVC index missing"
    exit 1
}

ls -lh *.pth *.index

echo
echo "[3/4] Inspecting RVC checkpoint..."

python - <<'PY'
import torch

path = "DanielUK_200e.pth"

try:
    checkpoint = torch.load(
        path,
        map_location="cpu",
        weights_only=True
    )

    if not isinstance(checkpoint, dict):
        raise TypeError("Unexpected checkpoint structure")

    print("Checkpoint keys:", list(checkpoint.keys()))

    for key in ("version", "f0", "sr", "info"):
        if key in checkpoint:
            print(f"{key}: {checkpoint[key]}")

    if "config" in checkpoint:
        config = checkpoint["config"]
        print("Configuration type:", type(config).__name__)
        if isinstance(config, (list, tuple)):
            print("Configuration entries:", len(config))

    if "weight" in checkpoint:
        print("Model weight tensors:", len(checkpoint["weight"]))

except Exception as e:
    print("Checkpoint inspection failed:", e)
    raise SystemExit(1)
PY

echo
echo "[4/4] Checking inference dependencies..."

python - <<'PY'
import importlib.util

packages = [
    "numpy",
    "scipy",
    "soundfile",
    "librosa",
    "faiss",
    "transformers",
    "torchaudio",
]

for name in packages:
    available = importlib.util.find_spec(name) is not None
    print(f"{name:15} {'OK' if available else 'MISSING'}")
PY

echo
echo "================================="
echo " SETUP CHECK COMPLETE"
echo "================================="
