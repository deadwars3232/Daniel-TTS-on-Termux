# Existing-device installation and rollback

Keep the working environment. Do not install upstream RVC requirements or run archived installers. `preservation/environment.json` records installed versions, not a portable pip lockfile. This work did not reinstall dependencies or download assets. Fresh-device installation is not verified and needs Termux-compatible wheels from the original providers.

Required assets remain at the paths in `instruction.md`: Daniel checkpoint, local Transformers HuBERT config/preprocessor/weights, RMVPE checkpoint, and Piper ONNX/config. Models are excluded from Git and retained on disk. The RVC source is a nested existing Git repository. Inference changes are committed on the nested `daniel/production-p0-p1` branch; the parent repository records its revision in `reports/rvc-revision.txt`. Retain the complete existing RVC checkout. `preservation/rvc-local.patch` captures pre-existing changes against that checkout.

The process-local `rvc-source/termux_compat.py` supplies the minimal Transformers models package and disabled GGUF loader before importing HuBERT. It is deliberately restricted to verified Transformers 4.44.2. The installed minimal `transformers/models/__init__.py` was left intact for other consumers; its original `.bak`, current contents and diff are preserved. The CLI no longer relies on executing that patched initializer. Doctor exercises imports without loading model weights. Always run doctor and an actual synthesis after any environment change.

Rollback code (keeps new files for investigation):

```sh
cd "$HOME/daniel_voice"
cp preservation/daniel-tts daniel-tts
cp preservation/rvc-source/convert_daniel.py rvc-source/convert_daniel.py
cp preservation/rvc-source/termux_compat.py rvc-source/termux_compat.py
```

HuBERT, RMVPE and the shared pipeline were not edited in this implementation; their known-good source copies are also in preservation. Existing site-packages were not modified. The installed command is a symlink and automatically follows launcher restoration. The old command overwrites outputs; choose a fresh output for rollback testing.

To recreate the launcher symlink on a device where it is absent:

```sh
ln -s "$HOME/daniel_voice/daniel-tts" "$PREFIX/bin/daniel-tts"
```

Do not overwrite an unrelated installed command. Model sources and licensing/commercial usage permissions remain unverified; this repository contains no model binaries.

Source reconstruction record: upstream RVC base `81eed5e8f68b6bed1789f682fe78cdd324495afc`, with `reports/rvc-production.patch` containing this device's production source additions and compatibility edits. Apply only to that clean base; do not apply on top of the existing production branch. This is source reproducibility, not a verified fresh-device package installation.
