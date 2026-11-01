import os
import sys
import time
import traceback
from pathlib import Path
from types import SimpleNamespace

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import termux_compat

import numpy as np
import soundfile as sf
import torch
from scipy.signal import resample_poly

from infer.hubert import load_hubert_model
from infer.module.models import SynthesizerTrnMs768NSFsid
from infer.vc.pipeline import Pipeline

ROOT = Path.home() / "daniel_voice"

# Required by infer/vc/pipeline.py.
os.environ["rmvpe_root"] = str(
    ROOT / "rvc-source" / "assets" / "rmvpe"
)
INPUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "base.wav"
OUTPUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "daniel_output.wav"
CHECKPOINT = ROOT / "DanielUK_200e.pth"

torch.set_num_threads(2)

def main():
    start = time.time()

    print("[1/6] Loading Daniel UK checkpoint...", flush=True)

    cpt = torch.load(
        CHECKPOINT,
        map_location="cpu",
        weights_only=False
    )

    config = list(cpt["config"])
    config[-3] = cpt["weight"]["emb_g.weight"].shape[0]

    print("[2/6] Initializing RVC synthesizer...", flush=True)

    net_g = SynthesizerTrnMs768NSFsid(
        *config,
        is_half=False
    )

    if hasattr(net_g, "enc_q"):
        del net_g.enc_q

    result = net_g.load_state_dict(cpt["weight"], strict=False)
    print("Missing keys:", len(result.missing_keys))
    print("Unexpected keys:", len(result.unexpected_keys))

    net_g = net_g.eval().to("cpu")

    print("[3/6] Loading HuBERT...", flush=True)

    hubert = load_hubert_model(
        device="cpu",
        is_half=False
    )

    print("[4/6] Preparing input audio...", flush=True)

    audio, sr = sf.read(INPUT, dtype="float32")

    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    if sr != 16000:
        from math import gcd
        divisor = gcd(sr, 16000)

        audio = resample_poly(
            audio,
            16000 // divisor,
            sr // divisor
        )

    audio = np.asarray(audio, dtype=np.float32)

    print(f"Input duration: {len(audio)/16000:.2f}s")

    # Configuration expected by the RVC inference pipeline.
    pipeline_config = SimpleNamespace(
        device="cpu",
        is_half=False,
        x_pad=1,
        x_query=6,
        x_center=38,
        x_max=41,
    )

    print("[5/6] Running RMVPE + RVC conversion...", flush=True)

    pipeline = Pipeline(
        tgt_sr=40000,
        config=pipeline_config
    )

    times = [0, 0, 0]

    with torch.inference_mode():
        output = pipeline.pipeline(
            model=hubert,
            net_g=net_g,
            sid=0,
            audio=audio,
            times=times,
            f0_up_key=0,
            f0_method="rmvpe",
            file_index="",
            index_rate=0.0,
            if_f0=1,
            tgt_sr=40000,
            resample_sr=0,
            rms_mix_rate=1.0,
            version="v2",
            protect=0.33,
        )

    print("[6/6] Saving WAV...", flush=True)

    output = np.asarray(output, dtype=np.float32)

    if output.size == 0:
        raise RuntimeError("RVC returned empty audio")

    output = np.nan_to_num(output)

    # Keep initial playback at a conservative level.
    peak = np.max(np.abs(output))
    if peak > 0:
        output = output / max(1.0, peak / 0.5)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    sf.write(
        OUTPUT,
        output,
        40000,
        subtype="PCM_16"
    )

    print()
    print("=== SUCCESS ===")
    print("Output:", OUTPUT)
    print("Duration:", round(len(output)/40000, 2), "seconds")
    print("Total time:", round(time.time()-start, 2), "seconds")
    print("Pipeline timings:", times)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\n[ERROR] Conversion failed:")
        traceback.print_exc()
        sys.exit(1)
