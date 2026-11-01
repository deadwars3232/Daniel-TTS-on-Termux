import os
import sys
import torch

BASE = os.path.expanduser("~/daniel_voice")
RVC = os.path.join(BASE, "rvc-source")

sys.path.insert(0, RVC)
os.chdir(RVC)

print("=== DANIEL UK RVC ENGINE TEST ===")
print("PyTorch:", torch.__version__)

files = {
    "Daniel UK": os.path.join(BASE, "DanielUK_200e.pth"),
    "HuBERT": "assets/hubert/hubert_base.pt",
    "RMVPE": "assets/rmvpe/rmvpe.pt",
    "Base speech": os.path.join(BASE, "base.wav"),
}

for name, path in files.items():
    if not os.path.isfile(path):
        print(f"[MISSING] {name}: {path}")
        sys.exit(1)

    size = os.path.getsize(path) / 1024**2
    print(f"[OK] {name}: {size:.1f} MB")

print("\n[1] Loading Daniel UK checkpoint...")

checkpoint = torch.load(
    files["Daniel UK"],
    map_location="cpu",
    weights_only=True
)

print("Version:", checkpoint["version"])
print("Sample rate:", checkpoint["sr"])
print("F0:", checkpoint["f0"])

print("\n[2] Testing RVC synthesizer import...")

try:
    from infer.module.models import SynthesizerTrnMs768NSFsid
    print("[OK] RVC v2 synthesizer imported")
except Exception as e:
    print("[FAIL] Synthesizer:", repr(e))

print("\n[3] Testing RMVPE import...")

try:
    from infer.rmvpe import RMVPE
    print("[OK] RMVPE imported")
except Exception as e:
    print("[FAIL] RMVPE:", repr(e))

print("\n[4] Testing RVC pipeline import...")

try:
    from infer.vc.pipeline import Pipeline
    print("[OK] RVC pipeline imported")
except Exception as e:
    print("[FAIL] Pipeline:", repr(e))

print("\n=== TEST COMPLETE ===")
