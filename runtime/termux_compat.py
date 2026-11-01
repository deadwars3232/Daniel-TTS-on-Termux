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

# Isolate the minimal models package in this process; never edit site-packages.
import importlib.util
from importlib.machinery import ModuleSpec
from importlib.metadata import version
from pathlib import Path

if version("transformers") != "4.44.2":
    raise RuntimeError("This compatibility layer requires the verified Transformers 4.44.2; run doctor before upgrading")
if "transformers.models" not in sys.modules:
    location = Path(importlib.util.find_spec("transformers").origin).parent / "models"
    package = types.ModuleType("transformers.models")
    package.__path__ = [str(location)]
    package.__package__ = "transformers.models"
    package.__spec__ = ModuleSpec("transformers.models", loader=None, is_package=True)
    package.__spec__.submodule_search_locations = package.__path__
    sys.modules["transformers.models"] = package
