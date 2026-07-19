"""The telescope. Blueprint Part I section 8.

Structured, configured once, IST timestamps, correlation ID per trial.

> **The telescope is not the ledger.**

The ledger is written by the engine as a first-class side effect; logging merely
*observes that the write happened*. Logs are things you can turn off. Ledgers are
not. **Any code path in which suppressing logs suppresses a ledger row is a build
failure** -- which is why nothing here returns a value an engine could come to
depend on, and why `configure` hands back a logger rather than a writer.

Secrets are redacted structurally, by key name, at any depth. Blueprint section 2
says secrets never appear in logs, and a rule enforced by remembering not to
print things is not enforced.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any, TextIO

# Asia/Kolkata is a fixed +05:30 offset with no daylight saving, so it is written
# directly rather than pulled from the platform tz database -- which is absent on
# some Windows installations, and section 5.2 calls Windows supported.
IST = timezone(timedelta(hours=5, minutes=30), name="IST")

LOGGER_NAME = "lab"
REDACTED = "[redacted]"

# Matched against the KEY, never the value. Value-shaped heuristics flag ordinary
# hashes and IDs, and a redactor that eats the correlation ID makes the telescope
# useless in exactly the situation it exists for.
SECRET_KEY_RE = re.compile(
    r"(secret|token|password|passwd|api[_-]?key|credential|authorization|private[_-]?key)",
    re.IGNORECASE,
)

# Attributes the stdlib puts on every record. Anything else a caller attaches via
# `extra=` is structured context and is emitted.
_STANDARD_ATTRS = frozenset(vars(logging.LogRecord("", 0, "", 0, "", None, None)))


def redact(payload: Any) -> Any:
    """Replace secret-looking values by key name, recursing through the structure.

    Redaction is by key rather than by value because the key is what the author
    declared the field to be. A value-based rule cannot tell an API token from a
    content hash, and both appear in this system.
    """
    if isinstance(payload, Mapping):
        return {
            key: REDACTED if SECRET_KEY_RE.search(str(key)) else redact(value)
            for key, value in payload.items()
        }
    if isinstance(payload, list | tuple):
        return [redact(item) for item in payload]
    return payload


class StructuredFormatter(logging.Formatter):
    """One JSON object per line, IST-stamped, with secrets removed."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=IST).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in vars(record).items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(redact(payload), default=str, sort_keys=True)


def configure(
    level: int | str = logging.INFO,
    stream: TextIO | None = None,
    correlation_id: str | None = None,
) -> logging.Logger:
    """Configure the telescope once, and return its logger. Blueprint section 8.

    Idempotent: existing handlers on the `lab` logger are removed before the new
    one is attached, so calling this twice in a process does not double every
    line. Propagation is disabled so records do not also reach a root handler
    some other library installed, which is how structured output becomes
    structured output plus a duplicate unstructured copy.

    `correlation_id` is stamped onto every record from this logger, which is what
    makes a trial's lines greppable as a unit.
    """
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    handler = logging.StreamHandler(sys.stderr if stream is None else stream)
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False

    if correlation_id is not None:
        logger.addFilter(_CorrelationFilter(correlation_id))
    return logger


class _CorrelationFilter(logging.Filter):
    """Stamps a correlation ID onto every record passing through the logger."""

    def __init__(self, correlation_id: str) -> None:
        super().__init__()
        self.correlation_id = correlation_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = self.correlation_id
        return True
