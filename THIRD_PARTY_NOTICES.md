# Third-party source and assets

`runtime/` contains the CPU inference subset from [RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI), upstream base `81eed5e8f68b6bed1789f682fe78cdd324495afc`, with local production changes recorded at `fb040f4b97b1fb7dace970cec0c3b7803d4007bb` in the original local checkout. The latter is a local provenance identifier, not a promise of a public upstream revision.

The original MIT copyright and permission notice is retained in [runtime/LICENSE](runtime/LICENSE). The subset includes the synthesizer, HuBERT adapter, RMVPE, shared pipeline and CUDA helper imported by those modules. Only the CPU/RMVPE path is supported. Local changes include NumPy compatibility, optional pitch/index dependencies, a Transformers 4.44.2 shim, and the reusable DanielEngine. Upstream files retain their attribution comments.

The root MIT license covers this project's original code and documentation. Dependencies retain their own licenses. Piper and FFmpeg are external executables and are not redistributed here. No model weights, voice datasets or generated audio are included. Model licenses and provenance must be established separately; this repository makes no grant of rights to a voice or checkpoint.
