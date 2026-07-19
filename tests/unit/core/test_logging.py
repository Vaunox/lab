"""The telescope. Blueprint Part I section 8."""

from __future__ import annotations

import io
import json
import logging

from lab.core.logging import IST, REDACTED, configure, redact


def _lines(stream: io.StringIO) -> list[dict[str, object]]:
    return [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]


def test_structured_and_redacted() -> None:
    """One JSON object per line, IST-stamped, with secrets removed by key name.

    Both halves are asserted together because they fail together: an unstructured
    line cannot be redacted reliably, and a redactor that runs before
    serialisation is redacting something other than what gets written.
    """
    stream = io.StringIO()
    logger = configure(level=logging.INFO, stream=stream, correlation_id="trial-0007")

    logger.info(
        "cost model resolved",
        extra={
            "trial_id": "abc123",
            "broker_api_key": "swordfish",
            "nested": {"password": "hunter2", "retries": 3},
        },
    )

    records = _lines(stream)
    assert len(records) == 1
    record = records[0]

    assert record["message"] == "cost model resolved"
    assert record["level"] == "INFO"
    assert record["trial_id"] == "abc123"
    assert record["correlation_id"] == "trial-0007"

    assert record["broker_api_key"] == REDACTED
    assert record["nested"] == {"password": REDACTED, "retries": 3}
    assert "swordfish" not in stream.getvalue()
    assert "hunter2" not in stream.getvalue()

    assert str(record["ts"]).endswith("+05:30"), record["ts"]


def test_redaction_is_by_key_not_by_value() -> None:
    """A content hash is not a credential.

    A value-shaped heuristic cannot tell an API token from a hash, and this
    system is full of hashes -- trial identity, the cost-model stamp, the ledger
    chain. A redactor that ate those would make the telescope useless in exactly
    the situation it exists for.
    """
    payload = {
        "trial_hash": "9f2b7c1e4a",
        "cost_model_hash": "deadbeef",
        "api_key": "9f2b7c1e4a",
    }

    assert redact(payload) == {
        "trial_hash": "9f2b7c1e4a",
        "cost_model_hash": "deadbeef",
        "api_key": REDACTED,
    }


def test_redaction_reaches_into_lists() -> None:
    """Nesting is not an escape hatch."""
    assert redact({"brokers": [{"name": "zerodha", "token": "abc"}]}) == {
        "brokers": [{"name": "zerodha", "token": REDACTED}]
    }


def test_configure_is_idempotent() -> None:
    """Calling it twice does not double every line.

    Section 8 says the telescope is configured *once*. In a process where it is
    configured twice -- a test session, an agent driving several runs -- doubled
    output is the visible symptom, and duplicated handlers on a shared logger is
    the cause.
    """
    first = io.StringIO()
    second = io.StringIO()

    configure(stream=first)
    logger = configure(stream=second)
    logger.info("once")

    assert _lines(first) == []
    assert len(_lines(second)) == 1


def test_logger_does_not_propagate_to_the_root() -> None:
    """Structured output must not arrive alongside an unstructured duplicate."""
    logger = configure(stream=io.StringIO())

    assert logger.propagate is False


def test_ist_is_a_fixed_offset() -> None:
    """Asia/Kolkata has no daylight saving, and no tz database is consulted.

    The platform tz database is absent on some Windows installations, and
    section 5.2 calls Windows supported rather than assumed.
    """
    assert IST.utcoffset(None).total_seconds() == 5.5 * 3600
