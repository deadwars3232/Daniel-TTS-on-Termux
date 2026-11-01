# Validation and release limits

Historical baseline on Android ARM64 / Python 3.14.8, 2026-11-01: a 2.30-second input produced 2.28-second mono PCM16 40 kHz output. Serial benchmark: first job 41.73 s, warm job 42.64 s, model construction 2.58 s, peak RSS 1584.9 MiB. Thermal conditions were not controlled; no speedup is claimed.

The 0.1.0 validation passed 12 CLI tests, real offline batch synthesis, positional synthesis, shared-storage text-file output, and deadline cleanup. Local logs and rollback copies were removed from the public tree during 0.2.0 preparation and retained under ignored `.local-backup/` on the development device. Git history also retains previously committed material.

Automated checks cannot establish voice similarity or listening quality. Before declaring a stable production release, verify clean-device dependency installation and model provenance, human listening (names, numbers, seams), sustained narration, Android background behavior and thermal performance. Input WAV conversion loads the entire input; text and job metrics are retained in memory. Forced termination can leave lock/staging directories; see README.md.

## 0.2.0 preparation checks — 2026-11-01

- 16 standard-library tests passed on the actual Termux Python 3.14.8 device.
- A clean 33-file source copy in a renamed directory passed the same suite and doctor using existing external assets; the old nested source was absent. This checks source completeness, not fresh dependency installation.
- The included runtime passed a real two-line Piper/FFmpeg/RVC batch with Python socket calls blocked: 2.50 seconds of non-silent mono PCM16 40 kHz audio, 82.84 seconds total, 1484.625 MiB peak RSS. Local sample: `reports/release-smoke.wav` (ignored). Peak amplitude 0.5.
- Installed symlink reported version 0.2.0. Compilation, documentation links and tracked diff whitespace checks passed. The public file set excludes models, audio, logs and local backups.
- GitHub-hosted CI has not run. No listening review or clean-device install was performed. Changes are prepared locally, not published. Old artifacts remain in Git history; working-tree cleanup does not rewrite history.
