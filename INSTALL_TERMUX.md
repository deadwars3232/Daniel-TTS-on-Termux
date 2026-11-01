# Install on native Termux

Supported inference target: Android ARM64, native Termux, CPU, Python 3.14. The CLI unit tests also run on Linux with Python 3.11–3.14. Windows, GPU inference, and other Piper command implementations are not supported.

## 1. Obtain the source

Clone this repository into a directory of your choice, then change into that directory. The inference source is included under `runtime/`; no submodules or upstream patch application is required.

```sh
python3 daniel-tts --help
python3 -m unittest discover -s tests -v
```

These commands require only Python's standard library.

## 2. Provide the inference environment

Keep a working installation intact. Do not run stock RVC requirements or upgrade the scientific stack blindly. The original Termux-specific wheels and a clean-device installation recipe have not been reproduced. This is a prerequisite checklist, not a portable pip lockfile.

Observed working versions on the development device:

| Component | Version |
|---|---|
| Python | 3.14.8 |
| PyTorch | 2.15.0 |
| NumPy | 2.5.4 |
| SciPy | 1.18.1 |
| soundfile | 0.14.0 |
| librosa | 1.0.0 |
| Transformers | **4.44.2** |
| huggingface-hub | 0.36.0 |
| safetensors | 0.8.0 |

Transformers 4.44.2 is enforced by the process-local compatibility shim. It does not edit site-packages. Other values above describe the installed device, not availability on PyPI or a tested version range.

Provide FFmpeg, libsndfile, eSpeak NG data, and the Termux-specific Piper CLI originally supplied by `gyroing/piper-tts-for-termux`. This Piper accepts `-m NAME -f FILE -- TEXT`, uses `PIPER_VOICE_PATH`, and writes **raw float32 little-endian mono at 22050 Hz**. Other Piper executables may use different flags/output formats. Validate the implementation before use.

FAISS, fairseq, numba, parselmouth and tokenizers are not required for the supported path. No dependency installer is bundled because installation on a clean device is not verified.

## 3. Supply trusted model assets

Use your own authorized local copies. No downloads are performed. The original Daniel checkpoint's authoritative source and redistribution permissions have not been established; the source license does not cover these assets. Record origins, licenses and checksums for your deployment.

Default paths relative to the checkout (or `DANIEL_ROOT`):

```text
DanielUK_200e.pth                 # RVC v2, f0-enabled, 40 kHz
rvc-source/assets/hubert_base/
  config.json
  preprocessor_config.json
  pytorch_model.bin              # compatible 768-dimensional HuBERT
rvc-source/assets/rmvpe/rmvpe.pt
```

The legacy `rvc-source/assets` location is retained for existing devices; only assets are read there. Code always loads from the checkout's `runtime/` directory.

Piper defaults to `$HOME/tts/models/en_GB-alan-medium.onnx` and its `.onnx.json` config. Override locations with `--checkpoint`, `--hubert-dir`, `--rmvpe-dir`, `--voice-dir`, and `--voice`. `ESPEAK_DATA_PATH` defaults to `$PREFIX/share/espeak-ng-data` (or Python's prefix if PREFIX is unset).

RVC uses pickle deserialization. Only load checkpoints you trust. The CLI is a local tool, not an upload service.

## 4. Verify and install the command

```sh
python3 daniel-tts doctor --json
python3 daniel-tts 'Hello world' hello.wav --json
python3 daniel-tts benchmark --output benchmark.wav --json
```

Listen to the output and check the voice and chunk seams. Doctor checks files and imports, not model integrity or audio quality. Allow about 1.6 GiB resident memory based on the recorded short benchmark, with additional headroom for longer input. Android can terminate background jobs.

Optional command symlink, from the checkout directory:

```sh
ln -s "$PWD/daniel-tts" "$PREFIX/bin/daniel-tts"
```

This fails safely if the destination exists. `python3 /path/to/checkout/daniel-tts` also works without a symlink. On systems without Termux executable rewriting, invoke Python explicitly if `/usr/bin/env` is unavailable.

## Updates, rollback and uninstall

Keep model assets separate from source changes. Back up local modifications before updating, inspect the changelog, then run tests, doctor and a synthesis. To roll back, use a separate checkout of your previous revision and point the command symlink at it; model path flags can reference existing assets.

To uninstall, remove only the symlink you created. The repository installs no packages or system services. Keep models and generated audio unless you intend to remove them separately.
