# Changelog

## 0.1.0 — 2026-11-01

- Preserved prototype, environment inventory and installed dependency patch in Git, with explicit rollback.
- Added CLI options, doctor, benchmark, preflight, output locks, atomic WAV publication, UTF-8 text files, cancellation and deadlines.
- Extracted reusable serial DanielEngine without changing RVC model, feature, pitch or gain settings.
- Added bounded text chunks and per-line batch narration, retaining models across chunks.
- Isolated Transformers compatibility in the process; left installed packages intact.
- Archived obsolete setup/repair scripts; removed only regenerable and duplicate artifacts documented in reports/cleanup.txt.
- Added operational tests and real-model evidence in reports/RESULTS.md. P2 tuning and human listening remain outstanding.
