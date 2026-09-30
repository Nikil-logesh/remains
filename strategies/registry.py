"""Stable strategy registry; unregistered routes cannot enter production."""

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Strategy:
    name: str
    version: str
    route: str
    adapter: Callable[..., dict[str, Any]]

    def run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.adapter(*args, **kwargs)


def _unavailable(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {
        "status": "not_available",
        "claims": [],
        "evidence": [],
        "errors": [{"code": "strategy_not_wired"}],
    }


_NAMES = (
    "registry_site",
    "sitemap_static",
    "static_homepage",
    "targeted_paths",
    "jsonld_opengraph",
    "search_candidates",
    "leader_founder_bridge",
    "browser_fallback",
    "pdf_fallback",
)
STRATEGIES = {
    name: Strategy(name, "1.0.0", name, _unavailable) for name in _NAMES
}


def get_strategy(name: str, version: str | None = None) -> Strategy:
    strategy = STRATEGIES[name]
    if version is not None and strategy.version != version:
        raise KeyError(f"strategy {name!r} version {version!r} is not registered")
    return strategy


def list_strategies() -> tuple[Strategy, ...]:
    return tuple(STRATEGIES.values())
