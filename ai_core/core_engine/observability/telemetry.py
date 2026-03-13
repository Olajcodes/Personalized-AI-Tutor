from __future__ import annotations

import logging
import time
from typing import Any


def now_ms() -> float:
    return time.perf_counter()


def log_timed_event(
    logger: logging.Logger,
    event: str,
    started_at: float,
    *,
    log_level: int = logging.INFO,
    **fields: Any,
) -> float:
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    rendered_fields = " ".join(
        f"{key}={_render_value(value)}" for key, value in fields.items() if value is not None
    ).strip()
    if rendered_fields:
        logger.log(log_level, "%s duration_ms=%.2f %s", event, duration_ms, rendered_fields)
    else:
        logger.log(log_level, "%s duration_ms=%.2f", event, duration_ms)
    return duration_ms


def _render_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.2f}"
    if isinstance(value, (list, tuple, set)):
        return "[" + ",".join(_render_value(item) for item in value) + "]"
    text = str(value).strip()
    return text.replace(" ", "_") if text else "empty"
