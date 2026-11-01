# P0/P1 implementation results — 2026-11-01

Read instruction.md completely before modifying source. Work performed on the actual Android ARM64 Termux installation, Python 3.14.8. No package installation, model download, model modification or site-packages edit occurred.

## Stages and verification

1. P0: snapshot original source, wrapper, existing RVC diff, installed Transformers initializer and .bak diff, and installed package versions. Parent preservation commits: 9ad682b and 0c8b585. Run original converter against base.wav before editing: passed, 2.2988 s input → 2.28 s mono PCM16 40 kHz, 39.94 s reported conversion time. Historical handoff baseline was 32.93 s; neither includes a controlled thermal comparison.
2. P0/P1: refactor the existing converter into DanielEngine, preserving settings; add process-local Transformers package initialization. Doctor imports succeeded before and after shim isolation. Existing installed initializer remains untouched. Nested RVC source commit: fb040f4b97b1fb7dace970cec0c3b7803d4007bb.
3. P1: add safe CLI and serial batch. Twelve unittest checks pass: positional parsing, text chunking, empty text, missing model, invalid output parent, truncated WAV, overwrite/failure preservation, cancellation cleanup, actual SIGTERM cancellation, active subprocess cancellation, failed subprocess, and one-engine batch reuse.
4. Real offline batch: two lines through Piper/FFmpeg/RVC, with Python socket connection methods replaced by failures. Passed; 83.54 s total, 2.60 s valid non-silent output. This blocks Python networking, not native subprocess networking; Piper uses existing local ONNX assets, and Transformers uses local-only/offline settings.
5. Serial fixture benchmark using final engine: passed, two 2.28 s outputs from the same 2.30 s fixture. No concurrent inference/import-check jobs. Device thermal state was not controlled.

| Metric | Measured |
|---|---:|
| Model construction | 2.58 s |
| First conversion job | 41.73 s |
| Model construction + first job | 44.31 s |
| Warm conversion job | 42.64 s |
| Whole two-job invocation, including imports | 97.63 s |
| Peak process RSS | 1584.9 MiB |
| First / warm RTF | 18.15 / 18.55 |
| First / warm synthesis stage | 32.99 / 33.27 s |

Model reuse is implemented, but these measurements do **not** establish a speedup. Keep two Torch threads and one BLAS/OpenMP thread until a controlled 1/2/3/4-thread test and listening review. First benchmark.json had overlapping doctor imports: retained as evidence, excluded from the serial comparison.

## Exact verification commands

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -u rvc-source/convert_daniel.py base.wav reports/baseline.wav
# The command above ran against the original converter before editing.
python -m unittest discover -s tests -v
daniel-tts --help
daniel-tts --version
daniel-tts doctor --json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python tests/offline_smoke.py --batch reports/script.txt --output reports/offline-batch.wav --json
daniel-tts benchmark --output reports/benchmark-serial.wav --json
daniel-tts --text-file reports/script.txt --output "$HOME/storage/downloads/daniel-p1-narration-20261101.wav" --quiet --json
```

Choose new output names when repeating, or explicitly add --overwrite. Operational evidence lives beside this report in logs and JSON. WAVs are local test artifacts excluded from source control.

## Changed files and cleanup

- daniel-tts: existing installed symlink target now launches Python CLI with early thread environment.
- daniel_cli.py: parser, paths/preflight, subprocess lifecycle, atomic writes/locks, batch/chunks, doctor, benchmark and status.
- rvc-source/convert_daniel.py: reusable engine, strict checkpoint match, finite/nonempty audio checks and preserved conversion parameters.
- rvc-source/termux_compat.py: version-guarded in-process Transformers models package shim; explicit GGUF rejection retained.
- tests/test_cli.py, tests/test_cancellation.py, tests/offline_smoke.py: operational and real-model checks.
- README.md, INSTALL_TERMUX.md, TROUBLESHOOTING.md, CHANGELOG.md: command contract, reproduction and rollback.
- .gitignore, preservation/, reports/: source safety snapshots, package/site-patch record, measurements and cleanup manifest.
- Existing infer/rmvpe.py and infer/vc/pipeline.py edits committed without altering their behavior. infer/hubert.py preserved unchanged.

Exact removed/archived paths: cleanup.txt. Model weights, optional index, known-good base.wav and daniel_output.wav retained. The other nested daniel_output.wav differs from the root fixture, so it was retained. Unrelated upstream RVC source was retained because deleting it could break imports. No checkpoint binaries committed.

## Remaining work and limits

Human listening, voice similarity, names/numbers, sentence seam quality, sustained long narration, thermal throttling and Android background survival are unverified. Text chunks split on whitespace and concatenate without crossfade. SIGKILL can leave stale locks/staging; see README. Input PCM WAV mode is not duration-bounded like text mode. Memory is roughly 1.55 GiB in this benchmark. Fresh-device packaging and usage/distribution rights remain unverified. Optional server, quantization and backend changes were deliberately deferred until P2 evidence supports them.

Storage/text-file check passed through the installed command: 2.44 s PCM16 mono 40 kHz output in Downloads, 65.52 s total. `--quiet --json` produced parseable JSON and empty stderr. See storage-text-file.json.

Legacy positional synthesis passed through installed `daniel-tts "Hello world" reports/positional.wav --json`: 1.06 s valid output, 54.78 s total. An actual CLI `--timeout 1` run returned 130 and left no final WAV or output lock. Human listening is still outstanding.

Tarsie documentation saved and committed locally (initial notes commit 074cfcb). Push to origin master failed because GitHub HTTPS credentials are unavailable. Vault checker reports one pre-existing frontmatter error in 2026-10-31.md; unrelated Obsidian settings were left alone. Diff whitespace checks pass for implementation files; preserved patch artifacts intentionally retain original CRLF/context whitespace.
