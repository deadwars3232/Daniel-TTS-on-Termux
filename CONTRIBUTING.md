# Contributing

Use Python 3.11 or newer on Linux/Termux for the standard-library CLI suite:

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q daniel_cli.py runtime tests
```

Keep changes focused, add a regression test for behavior changes, and describe commands and results in pull requests. Preserve atomic output and cancellation guarantees. Do not add models, private text, recordings, logs or credentials to Git. Do not run unreviewed upstream installers or modify site-packages.

Inference changes additionally need a real Termux test with authorized assets:

```sh
python3 daniel-tts doctor --json
python3 tests/offline_smoke.py --text 'Hello world.' --output reports/smoke.wav --json
```

The smoke helper blocks Python socket connections, not native process networking. Record device, versions, wall time, peak RSS and listening results. CI exercises CLI behavior with a fake engine and cannot establish inference quality or speed.

`runtime/` is vendored source, not a package to update independently. Preserve its license, compatibility changes and provenance when updating. Avoid formatting-only rewrites of upstream source.

Before a stable release: reproduce fresh-device setup, document authorized model acquisition, run sustained narration and thermal checks, and obtain listening review. Use GitHub issues for reproducible bugs without private input; see SECURITY.md for sensitive reports. Contributions are under the repository's MIT license.
