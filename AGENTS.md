# Repository guidance

Before work, read `~/storage/documents/Tarsie/AGENTS.md` when that vault is available, then the Daniel UK TTS Context and its latest handoff. The vault is private local context, never a runtime dependency; contributors without it can use README.md and docs/VALIDATION.md.

Keep inference offline and CPU-only. Preserve model assets and the installed Termux stack. Read THIRD_PARTY_NOTICES.md before editing runtime/. Run `python3 -m unittest discover -s tests -v`; inference changes also need doctor and a real synthesis. Never commit models, generated audio, local backups or private logs.
