# Daniel UK TTS — Production Engineering Handoff

**Status:** Working local proof of concept; **not yet production-ready**  
**Platform:** Android ARM64, native Termux (no proot, Ubuntu, GUI, or cloud inference)  
**Last verified:** 2026-11-01  
**Purpose:** Give Codex enough context to inspect the existing Termux installation and turn a functioning text-to-voice conversion prototype into a reliable, maintainable CLI suitable for narration and automation.

> **Codex:** The files described here exist **on the user's Termux device**, not necessarily in your own execution environment. Inspect the actual repository and installed packages before changing anything. Do not overwrite the working model files or assume this document is an exact snapshot of every source file.

## 1. Goal and current achievement

The user wants an offline command:

```bash
daniel-tts "Hello, my name is Daniel."
daniel-tts "Welcome to my channel!" "$HOME/storage/downloads/intro.wav"
```

The end-to-end workflow **has successfully run**:

```text
Text
  └─ Piper TTS: en_GB-alan-medium
      └─ raw float32 mono, 22,050 Hz
          └─ FFmpeg: proper PCM WAV
              └─ resample to 16,000 Hz using SciPy
                  └─ HuBERT speech features
                  └─ RMVPE fundamental frequency
                      └─ RVC v2 pitch-guided DanielUK model
                          └─ 40,000 Hz, mono, 16-bit PCM WAV
```

Successful recorded test (2.30-second input):

```text
[1/6] Loading Daniel UK checkpoint...
[2/6] Initializing RVC synthesizer...
Missing keys: 0
Unexpected keys: 0
[3/6] Loading HuBERT...
[4/6] Preparing input audio...
Input duration: 2.30s
[5/6] Running RMVPE + RVC conversion...
[6/6] Saving WAV...
=== SUCCESS ===
Output: /data/data/com.termux/files/home/daniel_voice/daniel_output.wav
Duration: 2.28 seconds
Total time: 32.93 seconds
Pipeline timings: [2.521026372909546, 4.935328006744385, 23.640809774398804]
```

The user subsequently confirmed the `daniel-tts` command worked. **Voice similarity, audio quality, performance under long-form loads, and deployment robustness have not been independently validated.**

## 2. Environment and dependency constraints

| Component | Known working environment |
|---|---|
| OS | Android, native Termux, ARM64 |
| Python | 3.14 |
| PyTorch | 2.15.0 |
| torchaudio | 2.11.1 |
| NumPy | 2.5.4 |
| SciPy | 1.18.1 |
| soundfile | 0.14.0 |
| librosa | 1.0.0 (some operations fail due to missing `soxr`) |
| ONNX Runtime | 1.31.1 |
| Transformers | 4.44.2, installed with `pip --no-deps` |
| huggingface-hub | 0.36.0 |
| safetensors | 0.8.0 |
| Piper | Termux-specific package from `gyroing/piper-tts-for-termux` |
| FFmpeg | Available and working |

**Not available / intentionally avoided:** `faiss`, `numba`, `fairseq`, `parselmouth`, and `tokenizers`. An attempted build of older `tokenizers` failed due to Python 3.14/PyO3 compatibility, and compiling a newer release was prohibitively slow. **Do not make these packages mandatory.** Avoid trying to `pip install` the stock RVC requirements indiscriminately; they are not aligned with this environment.

Use:

```bash
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
```

The conversion Python script also sets these variables, but setting them **before starting Python** is preferable for BLAS/OpenMP initialization.

## 3. Existing paths and models

```text
$HOME/daniel_voice/
├── DanielUK_200e.pth                        # RVC v2 model, ~52.7 MB
├── trained_IVF343_Flat_nprobe_1_DanielUK_200e_v2.index
│                                              # Optional FAISS index; not used
├── base.wav                                 # Known-good input fixture, 2.30 s
├── daniel_output.wav                        # Known-good output, 2.28 s
└── rvc-source/
    ├── convert_daniel.py                   # Working standalone conversion
    ├── convert_daniel.py.before_compat     # Backup, if present
    ├── termux_compat.py                    # Transformers compatibility shim
    ├── infer/
    │   ├── hubert.py                       # Transformers HuBERT adapter
    │   ├── rmvpe.py                        # Termux/NumPy compatibility edits
    │   ├── module/models.py                # RVC synthesizer
    │   └── vc/pipeline.py                  # RVC pipeline, optional imports patched
    └── assets/
        ├── hubert_base/
        │   ├── config.json
        │   ├── preprocessor_config.json
        │   └── pytorch_model.bin           # ~181 MB
        └── rmvpe/
            └── rmvpe.pt                    # ~172.8 MB

$HOME/tts/models/
├── en_GB-alan-medium.onnx
└── en_GB-alan-medium.onnx.json

$PREFIX/bin/daniel-tts                      # Working Bash wrapper
```

The RVC checkpoint was inspected and loaded with `Missing keys: 0` and `Unexpected keys: 0`. Relevant metadata:

```text
version = "v2"
sr      = "40k"
f0      = 1
speaker = 0
```

The optional `.index` file is **not used**: `file_index=""`, `index_rate=0.0`. Do not introduce FAISS as a production prerequisite without an explicit feature request.

## 4. Existing implementation

### 4.1 `daniel-tts` Bash wrapper

The working wrapper is installed at `$PREFIX/bin/daniel-tts` and:

1. Takes text as the first positional argument, optional output WAV as second.
2. Sets `PIPER_VOICE_PATH="$HOME/tts/models"` and `ESPEAK_DATA_PATH="$PREFIX/share/espeak-ng-data"`.
3. Creates a temporary directory with `mktemp -d` and deletes it via `trap ... EXIT`.
4. Calls Piper `-m en_GB-alan-medium -f "$TMP/base.raw" -- "$TEXT"`.
5. Calls FFmpeg with explicit raw audio format and a gain/limiter filter:

   ```bash
   ffmpeg -hide_banner -loglevel error -y \
     -f f32le -ar 22050 -ac 1 -i "$TMP/base.raw" \
     -af "volume=0.15,alimiter=limit=0.5" \
     -c:a pcm_s16le "$TMP/base.wav"
   ```

6. Changes directory to `$HOME/daniel_voice/rvc-source` and runs:

   ```bash
   python -u convert_daniel.py "$TMP/base.wav" "$OUTPUT"
   ```

7. Prints output path and success status. It uses `set -euo pipefail`.

**Important quirk:** This Termux Piper build emits **raw float32 audio** despite `-f` being a filename argument; it must be decoded as `f32le`, **not** treated as a normal WAV. The known-good sample rate is 22,050 Hz for the currently selected voice. Future code should validate actual Piper output format and model configuration rather than assuming all voices share this behavior.

### 4.2 `convert_daniel.py`

The Python entry point currently:

- Imports `termux_compat` **before** importing Transformers-dependent HuBERT code.
- Loads the RVC checkpoint using `torch.load(..., map_location="cpu", weights_only=False)`; this requires a **trusted** checkpoint file.
- Instantiates `SynthesizerTrnMs768NSFsid(*config, is_half=False)`.
- Adjusts `config[-3]` to the embedding speaker count and removes `enc_q` before loading model weights.
- Calls `load_state_dict(cpt["weight"], strict=False)` and prints missing/unexpected keys.
- Loads HuBERT with `load_hubert_model(device="cpu", is_half=False)`.
- Reads the input with `soundfile.read(..., dtype="float32")`, converts stereo to mono, and resamples to 16 kHz using `scipy.signal.resample_poly` and `math.gcd`.
- Sets `os.environ["rmvpe_root"]` to `$HOME/daniel_voice/rvc-source/assets/rmvpe`.
- Initializes `Pipeline(tgt_sr=40000, config=SimpleNamespace(device="cpu", is_half=False, x_pad=1, x_query=6, x_center=38, x_max=41))`.
- Calls `pipeline.pipeline` with `f0_method="rmvpe"`, `f0_up_key=0`, `sid=0`, `file_index=""`, `index_rate=0.0`, `if_f0=1`, `tgt_sr=40000`, `resample_sr=0`, `rms_mix_rate=1.0`, `version="v2"`, `protect=0.33`.
- Writes a 40 kHz PCM16 WAV via soundfile after sanitizing NaN/Inf and limiting peak level.

The RVC source's `infer/vc/pipeline.py` references `os.environ["rmvpe_root"]` to load `$rmvpe_root/rmvpe.pt`; this environment variable **must be set before inference**. The RVC pipeline contains optional `librosa.feature.rms` and `librosa.resample` paths; current parameters avoid the optional output resample and may avoid RMS mixing, but do not assume these functions are safe on Termux.

### 4.3 Compatibility patches already made

- `termux_compat.py` preloads a stub module named `transformers.modeling_gguf_pytorch_utils`, preventing a GGUF/tokenizers import chain when loading `HubertModelWithFinalProj`. It should reject actual GGUF loading explicitly.
- `transformers/models/__init__.py` was modified to avoid unrelated T5 imports; a `.bak` exists. **This modifies installed site-packages and is fragile across upgrades.** Prefer isolating or eliminating this patch in production after testing.
- `infer/vc/pipeline.py` treats `parselmouth` as optional; a missing `faiss` is also tolerated. RMVPE remains the required pitch estimator.
- `infer/rmvpe.py` has changes to avoid unavailable numba/librosa dependencies, using NumPy-compatible alternatives. Its pitch inference was tested successfully on a 200 Hz sine signal.
- The conversion script replaced `librosa.resample` with `scipy.signal.resample_poly` to avoid `ModuleNotFoundError: soxr`.

**Do not remove compatibility edits until the replacement is verified on the actual device.**

## 5. Verified components and benchmark

- RVC model weights: fully matched (`missing=0`, `unexpected=0`).
- HuBERT CPU test: 1 second input produced `(1, 49, 768)` features; ~1.8 seconds inference in that isolated test.
- RMVPE CPU test: 2 seconds of 200 Hz sine produced approximately 200 Hz estimated pitch; ~2.8 seconds in that isolated test.
- End-to-end RVC conversion: 2.30 seconds input → 2.28 seconds output in **32.93 seconds** total.
- Pipeline timing values: **2.52 s** features, **4.94 s** pitch, **23.64 s** synthesis. These sum to ~31.10 seconds; remaining time includes loading and other overhead. **The RVC synthesis stage is the main measured bottleneck** (~72% of total wall time). These are single-run numbers, not a controlled benchmark.
- The user confirmed the wrapper ran successfully. Listening tests and quality ratings have not been recorded.

## 6. Production roadmap — priority order

### P0 — Preserve and stabilize the working prototype

- Create a versioned repository/branch; record a `git diff` of all source and site-packages patches before changing anything.
- Copy the known-good `convert_daniel.py`, `termux_compat.py`, wrapper, and any local RVC edits into source control. **Do not commit checkpoint/model binaries unless distribution rights and storage constraints are clear.**
- Make model paths configurable with defaults based on `$HOME`; avoid hard-coded `/data/data/...` paths except Termux shebang where appropriate.
- Replace ad hoc import-time patching with a documented, reproducible compatibility layer or a carefully tested supported dependency configuration.
- Validate model paths and audio files **before** loading hundreds of megabytes of models. Report actionable errors.
- Preserve the current working command and keep an explicit rollback path.

### P1 — Reliable CLI and operational behavior

Implement a proper CLI (Python CLI, or a small robust shell frontend plus Python backend):

```text
daniel-tts "Hello" [output.wav]
daniel-tts --text "Hello" --output hello.wav
daniel-tts --text-file script.txt --output narration.wav
daniel-tts --voice en_GB-alan-medium --output narration.wav "Hello"
daniel-tts --help
daniel-tts --version
daniel-tts doctor
daniel-tts benchmark
```

Recommended behavior:

- Preserve backward compatibility with the current two-positional-argument syntax.
- Handle empty text, missing Piper/FFmpeg/model files, invalid output locations, interruptions, and conversion errors with nonzero exit codes.
- Use safe temporary files and cleanup on success, error, and interruption.
- Never print success if the WAV does not exist or is empty.
- Write output **atomically**: produce in a temp file and rename into place only after validation, to avoid corrupting an existing output on failure.
- Quote all shell arguments; do not invoke shell interpolation on user-supplied text.
- Add `--overwrite` policy (default: do not overwrite without permission, or clearly document chosen behavior).
- Offer `--quiet`, `--verbose`, and optional `--json` machine-readable status.
- Use predictable UTF-8 text handling and support punctuation and long scripts.
- Ensure output files under `~/storage/...` are handled correctly after Termux storage permission is granted.

### P1 — Reuse loaded models for multiple utterances

**Major opportunity:** The current wrapper launches a new Python process and loads the RVC checkpoint and HuBERT for each invocation. For batch narration, provide a persistent local worker that loads the synthesizer, HuBERT, and RMVPE **once**, then processes a queue of jobs.

- First implement a single-process batch mode (`--text-file`, `--batch`) to avoid reloads across sentences.
- Optionally implement a localhost-only worker/server with explicit start/stop/status commands; **do not expose an unauthenticated server on `0.0.0.0`**.
- Make job cancellation, timeouts, and graceful shutdown work on Android.
- Monitor memory usage and avoid loading duplicate model instances.
- Prefer serial inference by default; concurrent CPU jobs may cause memory pressure and slowdowns.

### P2 — Performance optimization with benchmarks

**Measure before changing.** Compare both end-to-end wall time and stage timings, peak RSS, and output quality:

1. Benchmark `torch.set_num_threads(1, 2, 3, 4)` and appropriate OpenMP settings on the actual phone.
2. Compare cold-start and warm-start inference separately.
3. Profile synthesizer CPU ops and tensor allocations; optimize only confirmed hotspots.
4. Test `torch.inference_mode()`, avoiding unnecessary tensor copies and data conversions.
5. Experiment with pitch extraction settings only if quality remains acceptable.
6. Investigate optional quantization/alternative backends **only if supported by the model and validated for audio quality**; do not assume ONNX export will automatically work or improve speed.
7. For long input, implement bounded chunking with appropriate overlap/crossfade to avoid audible seams; use RVC's existing padding and segmentation behavior as a starting point.
8. Consider Android thermal throttling and background process restrictions during long runs.

Suggested benchmark report: `input_seconds`, `total_seconds`, `real_time_factor = total_seconds/input_seconds`, `hubert_seconds`, `rmvpe_seconds`, `synthesis_seconds`, `peak_rss_mb`, `threads`, `device`, and `success`.

### P2 — Audio quality and narration features

- Validate Piper gain/limiter behavior; the current `volume=0.15,alimiter=limit=0.5` is a working configuration, **not** a universally optimal audio setting.
- Add configurable speaking rate, pauses, sentence splitting, pitch transpose (`f0_up_key`), protection, and optional final loudness normalization.
- Implement audio checks for silence, clipping, NaNs, peak level, output sample rate, and unexpected duration changes.
- Offer a consistent output contract: mono PCM16 WAV at 40 kHz by default, with optional FFmpeg export to other formats.
- Compare a small set of spoken phrases by listening, especially names, numbers, punctuation, and longer narration.
- Avoid overprocessing that makes the output sound distorted or metallic.
- Do not silently substitute another voice if a requested model is missing.

### P3 — Distribution, testing, and documentation

- Package installation and uninstall scripts tailored for native Termux.
- Provide an environment doctor with concise compatibility checks, not a dependency installer that recompiles everything.
- Add unit tests for argument parsing, path handling, resampling, and WAV validation.
- Add integration tests with short known-good fixtures; skip large-model tests if model assets are unavailable.
- Add a `README.md`, `INSTALL_TERMUX.md`, `TROUBLESHOOTING.md`, `CHANGELOG.md`, and sample scripts.
- Document model sources, licenses, and usage/distribution permissions. **Do not assume the Daniel voice model or reference voice can be redistributed or used commercially without checking applicable rights.**
- If output is used publicly, use appropriate attribution/disclosure where required and avoid misleading impersonation.

## 7. Known failures and lessons learned

| Failure | Root cause | Working resolution |
|---|---|---|
| `ModuleNotFoundError: tokenizers` during HuBERT import | Transformers GGUF import chain | `termux_compat` stub + minimal `transformers.models` init patch |
| `ModuleNotFoundError: soxr` | `librosa.resample()` lazy-imports soxr | `scipy.signal.resample_poly()` |
| `KeyError: 'rmvpe_root'` | RVC pipeline requires environment variable | Set `rmvpe_root` to `.../assets/rmvpe` |
| Missing `faiss` | Optional index support | `file_index=""`, `index_rate=0.0` |
| Missing `parselmouth` | Optional pitch estimator | RMVPE path only |
| `numba` unavailable | Some RVC/RMVPE/librosa paths expect it | Existing RMVPE NumPy patch; avoid affected code paths |
| Piper output not a WAV | Termux Piper emits raw f32le | Explicit FFmpeg input format `-f f32le -ar 22050 -ac 1` |

The `FutureWarning` about `torch.nn.utils.weight_norm` is **not an inference failure**. Do not prioritize removing it over stability.

## 8. Acceptance criteria

The production implementation is complete when all of the following are demonstrated **on the real Termux device**:

- [ ] `daniel-tts "Hello world"` produces a playable, nonempty, valid 40 kHz PCM16 WAV.
- [ ] `daniel-tts "Hello world" ~/storage/downloads/hello.wav` works with appropriate storage permissions.
- [ ] `daniel-tts --text-file script.txt --output narration.wav` works with multiline text.
- [ ] The CLI returns clear errors and nonzero status for missing models, empty input, invalid paths, and failed subprocesses.
- [ ] Interrupted jobs remove temp files and do not leave partially written final outputs.
- [ ] Running twice with the same text produces outputs of reasonable duration without silent corruption.
- [ ] Batch mode reuses loaded RVC/HuBERT/RMVPE models rather than reloading per sentence.
- [ ] No root, proot, Ubuntu, GUI, network request, FAISS, fairseq, numba, parselmouth, or tokenizers is required for inference.
- [ ] A reproducible installation procedure and rollback instructions exist.
- [ ] Benchmark report compares the new implementation to the 32.93-second / 2.30-second baseline on the same device.
- [ ] Human listening tests confirm the generated voice is intelligible and suitable for the user's intended narration.

## 9. Exact instructions for Codex

> You are the lead Python/Termux engineer. Transform the **existing working** offline Daniel UK Piper→RVC prototype into a production-grade, maintainable native Android Termux CLI. **Do not start from scratch or reinstall the model stack.** First inspect the actual files (`$PREFIX/bin/daniel-tts`, `$HOME/daniel_voice/rvc-source/convert_daniel.py`, `termux_compat.py`, `infer/hubert.py`, `infer/rmvpe.py`, `infer/vc/pipeline.py`) and confirm current working behavior. Create a safety backup and a prioritized implementation plan. Then implement P0 and P1 in small, testable changes; run smoke tests after each change. Preserve the verified model configuration (RVC v2, 40 kHz, f0 enabled, RMVPE, HuBERT 768-dimensional features, FAISS disabled). Do not make unavailable dependencies mandatory. Provide a `doctor` command, meaningful error handling, atomic outputs, `--text-file` batch mode with model reuse, documentation, and a benchmark harness. Only then propose optional CPU optimizations. Never modify/delete model weights or assume site-packages patches survive updates. Report every changed file, command to test it, measured results, and remaining limitations.

## 10. First commands Codex should run on the device

```bash
cd "$HOME/daniel_voice/rvc-source"
printf 'Python: '; python --version
printf 'Piper: '; command -v piper
printf 'FFmpeg: '; command -v ffmpeg
printf 'CLI: '; command -v daniel-tts
ls -lh "$HOME/daniel_voice/DanielUK_200e.pth" \
       assets/rmvpe/rmvpe.pt \
       assets/hubert_base/pytorch_model.bin
sed -n '1,240p' "$PREFIX/bin/daniel-tts"
sed -n '1,240p' convert_daniel.py
sed -n '1,200p' termux_compat.py
```

These are inspection commands, not a request to reinstall packages. Codex should then compare the implementation to this handoff and propose an incremental change set.
