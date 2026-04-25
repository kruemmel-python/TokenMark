from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
import importlib

Hook = Callable[..., Any]

@dataclass
class PluginManager:
    hooks: dict[str, list[Hook]] = field(default_factory=lambda: {
        "on_init": [],
        "pre_compile": [],
        "post_compile": [],
        "pre_render": [],
        "post_render": [],
        "pre_render_segment": [],
    })

    def register(self, hook_name: str, fn: Hook) -> None:
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(fn)

    def call(self, hook_name: str, *args: Any, **kwargs: Any) -> Any:
        result = None
        for fn in self.hooks.get(hook_name, []):
            result = fn(*args, **kwargs)
        return result

    def mutate_segments(self, hook_name: str, segments: list[Any], **kwargs: Any) -> list[Any]:
        for fn in self.hooks.get(hook_name, []):
            out = fn(segments, **kwargs)
            if out is not None:
                segments = out
        return segments

    def mutate_segment(self, segment: Any, **kwargs: Any) -> Any:
        for fn in self.hooks.get("pre_render_segment", []):
            out = fn(segment, **kwargs)
            if out is not None:
                segment = out
        return segment

def load_plugin_manager(cfg: dict[str, Any] | None = None) -> PluginManager:
    cfg = cfg or {}
    pm = PluginManager()
    for name in cfg.get("plugins", []):
        try:
            mod = importlib.import_module(name)
            if hasattr(mod, "register"):
                mod.register(pm)
            else:
                # Backward-compatible convention: module-level functions named like hooks.
                for hook in list(pm.hooks):
                    fn = getattr(mod, hook, None)
                    if callable(fn):
                        pm.register(hook, fn)
        except Exception as e:
            print(f"[tokenmark] plugin load failed: {name}: {e}")
    return pm
