# Changelog

## 0.2.0 — Unreleased

- Include the licensed CPU inference source in a normal clone.
- Resolve the launcher relative to its real checkout, including symlinks; DANIEL_ROOT selects assets only.
- Make default benchmarks self-contained with a built-in sentence and repeat text benchmarks for warm measurements.
- Preserve dangling output symlinks unless overwrite is explicitly requested.
- Add CI, regression tests, contribution/security guidance and explicit installation prerequisites.
- Remove obsolete installers, backups and device reports from the public tree; retain local recovery copies.

## 0.1.0 — 2026-11-01

- Add offline CLI, doctor, benchmark, preflight, output locks, atomic WAV publication, UTF-8 text files, cancellation and deadlines.
- Reuse RVC/HuBERT/RMVPE across serial narration chunks.
- Isolate Transformers compatibility in-process without changing installed packages.
