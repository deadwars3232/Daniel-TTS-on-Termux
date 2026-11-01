# Troubleshooting

- Run `daniel-tts doctor --json` for installed imports, versions and required file checks. It does not claim model integrity or voice quality; use synthesis for that.
- Missing files: restore the original assets or supply the documented path flags. No automatic downloads are attempted.
- Storage permission: verify Termux can write the chosen directory under `$HOME/storage`; grant Android storage permission if needed. Use the actual directory spelling on this device.
- Output exists: choose a fresh filename or explicitly pass `--overwrite`.
- Busy output: another process owns the output directory lock. After a forced kill, confirm the old process has stopped before removing the lock.
- Tokenizers/T5/GGUF import error: confirm `termux_compat` is imported first and Transformers remains 4.44.2. Do not reinstall tokenizers to fix this pipeline.
- soxr/FAISS/numba/parselmouth: none is required by the preserved RMVPE-only, index-disabled, no-output-resampling path. Do not enable alternative paths without testing.
- Bad voice or seams: retain samples for listening comparison. Chunk boundaries and source Piper prosody still need human review.
- Slow jobs: compare first and warm job timings under the same device temperature/load. Avoid concurrent CPU benchmarks. No thermal/background-process guarantees are possible.
