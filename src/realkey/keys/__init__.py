"""Concrete key-family implementations."""

from importlib import import_module

_BUILTIN_MODULES = (
    "assa",
    "dom",
    "miwa",
    "opnus",
    "paclock",
    "sargent_and_greenleaf",
    "schlage",
    "vsr",
)


def load_all() -> None:
    """Import every built-in key family and populate the key registry."""
    for module_name in _BUILTIN_MODULES:
        import_module(f"{__name__}.{module_name}")


__all__ = ["load_all"]
