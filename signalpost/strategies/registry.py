from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Strategy:
    name: str
    version: str
    route: str
    adapter: Callable[..., Any]

    def run(self, *args: Any, **kwargs: Any) -> Any:
        return self.adapter(*args, **kwargs)


def _stub(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """An unavailable connector never guesses: it returns an explicit miss."""
    return {"claims": [], "evidence": [], "status": "not_implemented",
            "errors": [{"code": "connector_unavailable"}]}


_ROUTES = (
    ("registry", "1.0.0"),
    ("website", "1.0.0"),
    ("financial", "1.0.0"),
    ("announcements", "1.0.0"),
    ("accounts", "1.0.0"),
    ("llm", "1.0.0"),
)
_strategies = {name: Strategy(name, version, name, _stub) for name, version in _ROUTES}
STRATEGIES = _strategies


def register_strategy(strategy: Strategy) -> None:
    if not strategy.name or not strategy.version:
        raise ValueError("strategy name and version are required")
    _strategies[strategy.name] = strategy


def get_strategy(name: str, version: str | None = None) -> Strategy:
    try:
        strategy = _strategies[name]
    except KeyError as exc:
        raise KeyError(f"unknown strategy: {name}") from exc
    if version is not None and strategy.version != version:
        raise KeyError(f"strategy {name!r} version {version!r} is not registered")
    return strategy


def list_strategies() -> tuple[Strategy, ...]:
    return tuple(_strategies[name] for name, _ in _ROUTES if name in _strategies)
