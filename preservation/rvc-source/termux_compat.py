"""Compatibility workaround for RVC HuBERT on Termux."""

import sys
import types

module_name = "transformers.modeling_gguf_pytorch_utils"

if module_name not in sys.modules:
    stub = types.ModuleType(module_name)

    def load_gguf_checkpoint(*args, **kwargs):
        raise RuntimeError(
            "GGUF loading is disabled in this Termux RVC setup."
        )

    stub.load_gguf_checkpoint = load_gguf_checkpoint
    sys.modules[module_name] = stub
