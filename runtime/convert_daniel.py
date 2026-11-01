import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import termux_compat

import numpy as np
import soundfile as sf
import torch
from scipy.signal import resample_poly

from infer.hubert import load_hubert_model
from infer.module.models import SynthesizerTrnMs768NSFsid
from infer.vc.pipeline import Pipeline

class DanielEngine:
    """Serial CPU engine retaining RVC, HuBERT and lazy RMVPE."""
    def __init__(self, checkpoint, hubert_dir, rmvpe_dir, threads=2):
        torch.set_num_threads(threads)
        os.environ["rmvpe_root"] = str(rmvpe_dir)
        import infer.hubert
        infer.hubert.HUBERT_MODEL_PATH = Path(hubert_dir)
        cpt = torch.load(
            checkpoint,
            map_location="cpu",
            weights_only=False
        )

        if cpt.get("version") != "v2" or cpt.get("f0") != 1 or cpt["config"][-1] != 40000:
            raise ValueError("Expected v2, f0-enabled, 40 kHz checkpoint")
        config = list(cpt["config"])
        config[-3] = cpt["weight"]["emb_g.weight"].shape[0]

        print("Initializing RVC synthesizer...", flush=True)

        net_g = SynthesizerTrnMs768NSFsid(
            *config,
            is_half=False
        )

        if hasattr(net_g, "enc_q"):
            del net_g.enc_q

        result = net_g.load_state_dict(cpt["weight"], strict=False)
        print("Missing keys:", len(result.missing_keys))
        print("Unexpected keys:", len(result.unexpected_keys))

        if result.missing_keys or result.unexpected_keys:
            raise ValueError("Checkpoint weights do not match")
        self.net_g = net_g.eval().to("cpu")

        print("Loading HuBERT...", flush=True)

        self.hubert = load_hubert_model(
            device="cpu",
            is_half=False
        )

        # Configuration expected by the RVC inference pipeline.
        pipeline_config = SimpleNamespace(
            device="cpu",
            is_half=False,
            x_pad=1,
            x_query=6,
            x_center=38,
            x_max=41,
        )

        print("Initializing reusable RMVPE/RVC pipeline...", flush=True)

        self.pipeline = Pipeline(
            tgt_sr=40000,
            config=pipeline_config
        )


    def convert(self, input_path, output_path):
        start = time.perf_counter()
        audio, sr = sf.read(input_path, dtype="float32")

        if audio.size < 32 or not np.isfinite(audio).all():
            raise ValueError("Input is too short or contains NaN/Inf")
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

        times = [0, 0, 0]

        with torch.inference_mode():
            output = self.pipeline.pipeline(
                model=self.hubert,
                net_g=self.net_g,
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

        print("Saving converted chunk...", flush=True)

        output = np.asarray(output, dtype=np.float32)

        if output.size == 0:
            raise RuntimeError("RVC returned empty audio")

        if not np.isfinite(output).all():
            raise ValueError("RVC returned NaN/Inf")

        # Keep initial playback at a conservative level.
        peak = np.max(np.abs(output))
        if peak == 0:
            raise ValueError("RVC returned silent audio")
        output = output / max(1.0, peak / 0.5)

        sf.write(output_path, output, 40000, subtype="PCM_16")
        return {"input_seconds": len(audio)/16000, "output_seconds": len(output)/40000, "conversion_seconds": time.perf_counter()-start, "hubert_seconds": times[0], "rmvpe_seconds": times[1], "synthesis_seconds": times[2]}

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from daniel_cli import main
    raise SystemExit(main(["--input-wav", *(sys.argv[1:2] or [str(Path.home()/"daniel_voice/base.wav")]), "--output", *(sys.argv[2:3] or [str(Path.home()/"daniel_voice/daniel_output.wav")])]))
