"""Plugin system coordination."""
from __future__ import annotations

from importlib import import_module
from typing import Dict, Type

from tova.plugins.base.plugin import BasePlugin


class PluginManager:
    """Loads and tracks plugins by dotted path."""

    def __init__(self) -> None:
        self.name_to_plugin: Dict[str, Type[BasePlugin]] = {}

    def register(self, name: str, dotted_path: str) -> None:
        module_path, class_name = dotted_path.rsplit(".", 1)
        module = import_module(module_path)
        plugin_cls = getattr(module, class_name)
        if not issubclass(plugin_cls, BasePlugin):
            raise TypeError("Plugin must inherit from BasePlugin")
        self.name_to_plugin[name] = plugin_cls

    def create(self, name: str, **kwargs) -> BasePlugin:
        plugin_cls = self.name_to_plugin[name]
        return plugin_cls(**kwargs) 