# Daniel UK TTS for native Termux

Offline speech generation on Android ARM64: Piper → HuBERT/RMVPE → RVC, producing mono PCM16 WAV at 40 kHz. Includes serial batch narration, model reuse, atomic output, cancellation, deadlines, and JSON status.

**Status:** tested on an existing native Termux Python 3.14 installation. Fresh-device dependency installation and human audio-quality review remain release gates; this is not a verified one-command install. See [installation](INSTALL_TERMUX.md) before running inference. Source is MIT licensed; model weights are not included or licensed by this repository.

From a checkout, run `python3 daniel-tts --help`. After following the installation instructions:

```sh
daniel-tts --help
daniel-tts --version
daniel-tts doctor
daniel-tts 'Hello world' hello.wav
daniel-tts --text 'Hello world' --output "$HOME/storage/downloads/hello.wav"
daniel-tts --text-file script.txt --output narration.wav
daniel-tts --batch script.txt --output narration.wav --overwrite --json
daniel-tts benchmark --output benchmark.wav --json
python -m unittest discover -s tests -v
```

Outputs are mono PCM16 WAV at 40 kHz. Existing outputs require `--overwrite`. Relative paths refer to the invoking directory. Parent directories are created. A same-directory staging file is validated and renamed into place; failure leaves the previous output intact. A per-output directory lock prevents simultaneous CLI writers. External programs that ignore the lock must not write the same destination concurrently.

`--text-file` reads UTF-8 (optional BOM), combines whitespace and splits into at most 350-character chunks. `--batch` processes each nonempty line, splitting long lines similarly. Both join chunks into one narration WAV, loading RVC and HuBERT once and retaining RMVPE after its first use. Inference is serial. Text chunks are bounded; all text and job metrics are currently retained in memory. Word boundaries do not guarantee natural narration seams: listen before publishing. No extra silence or crossfade is inserted.

`--timeout SECONDS` applies to the entire invocation. Ctrl-C and SIGTERM cancel work, kill active Piper/FFmpeg subprocess groups, and clean staging files. Native CPU operations may delay Python signal handling. SIGKILL, Android force-stop or power loss cannot run cleanup: after confirming no job is active, remove the matching `.OUTPUT.wav.lock` directory and abandoned `.daniel-*` directory. Restart the job; there is no resume protocol.

`--json` emits one status object on stdout; diagnostic output goes to stderr. `--quiet` suppresses inference logs and success text, but still returns requested JSON and errors. `--verbose` includes subprocess diagnostics and tracebacks. Parse errors use argparse's stderr output and exit 2; operational errors exit 1; cancellation/deadline exit 130.

Model paths: `DANIEL_ROOT` defaults to the checkout directory and controls asset lookup only; flags `--checkpoint`, `--hubert-dir`, `--rmvpe-dir`, `--voice-dir` override assets. `--voice` selects a Piper model by name, with no silent fallback. Only 22050 Hz Piper voices are verified with this build's raw f32le output. The existing volume/limiter and conservative RVC peak handling are preserved. Only use trusted checkpoint files: PyTorch loads the existing RVC pickle format.

CPU defaults remain two PyTorch threads and one BLAS/OpenMP thread. `--threads 1..4` allows measured comparisons; no speedup is promised. `benchmark` defaults to two syntheses of a built-in sentence in the same process; `benchmark --input-wav sample.wav` converts a supplied fixture twice and concatenates them into its output. JSON separates model load, first conversion (including lazy RMVPE load), warm conversion, stage timings, RTF and peak process RSS. Total time includes CLI imports/preflight; `cold_seconds` includes engine construction and first job, but not initial imports. `--input-wav` accepts a PCM WAV to convert without Piper. Benchmarks using text run the requested text sequence twice and include Piper and FFmpeg job time. This doubles the text in the benchmark output.

See [INSTALL_TERMUX.md](INSTALL_TERMUX.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md), [CHANGELOG.md](CHANGELOG.md), [CONTRIBUTING.md](CONTRIBUTING.md), and [validation](docs/VALIDATION.md).


The `runtime/` directory contains the CPU inference subset and Termux compatibility changes from RVC; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). No nested checkout or source download is needed. GPU, training, FAISS retrieval, and alternative pitch estimators are outside the supported CLI contract.
