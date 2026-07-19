"""Layered configuration and the secret boundary. Blueprint Part I section 2."""

from __future__ import annotations

from pathlib import Path

import pytest

from lab.core.config import (
    ConfigError,
    MissingSecretError,
    environment_overrides,
    get_secret,
    load_config,
)


def _write(config_dir: Path, name: str, body: str) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / name).write_text(body, encoding="utf-8")


def test_layered_override(tmp_path: Path) -> None:
    """`default.yaml` <- `{env}.yaml` <- environment, in that order.

    The nested case is the one that matters. `ledger.path` is overridden while
    `ledger.fsync` is not, and the untouched sibling must survive: a layer that
    replaced the whole `ledger` block would drop `fsync` back to its code
    default, invisibly, and Inviolable Rule 2 is specifically about that setting.
    """
    config_dir = tmp_path / "config"
    _write(
        config_dir,
        "default.yaml",
        "ledger:\n  path: ledger.jsonl\n  fsync: true\nuniverse:\n  size: 500\n",
    )
    _write(config_dir, "backtest.yaml", "ledger:\n  path: runs/backtest.jsonl\n")

    resolved = load_config(
        env="backtest",
        config_dir=config_dir,
        environ={"LAB_UNIVERSE__SIZE": "100"},
    )

    assert resolved["ledger"]["path"] == "runs/backtest.jsonl"
    assert resolved["ledger"]["fsync"] is True, "an untouched sibling key was discarded"
    assert resolved["universe"]["size"] == 100
    assert isinstance(resolved["universe"]["size"], int), "the env layer changed the type"


def test_environment_layer_wins_over_every_file(tmp_path: Path) -> None:
    """The highest layer is the environment, and precedence is asserted, not assumed."""
    config_dir = tmp_path / "config"
    _write(config_dir, "default.yaml", "ledger:\n  path: from-default\n")
    _write(config_dir, "backtest.yaml", "ledger:\n  path: from-env-file\n")

    resolved = load_config(
        env="backtest",
        config_dir=config_dir,
        environ={"LAB_LEDGER__PATH": "from-environment"},
    )

    assert resolved["ledger"]["path"] == "from-environment"


def test_absent_layers_contribute_nothing(tmp_path: Path) -> None:
    """A missing optional layer is not an error. A malformed one is."""
    assert load_config(env="default", config_dir=tmp_path / "absent", environ={}) == {}

    config_dir = tmp_path / "config"
    _write(config_dir, "default.yaml", "just a string, not a mapping\n")

    with pytest.raises(ConfigError):
        load_config(env="default", config_dir=config_dir, environ={})


def test_secrets_never_enter_the_config_object() -> None:
    """`LAB_SECRET_*` is excluded from the environment layer.

    Anything in the config object is a candidate for being logged, serialised
    into a run record, or printed in a traceback. Keeping secrets out of that
    object is what makes "secrets never appear in logs" structural rather than a
    matter of remembering.
    """
    overrides = environment_overrides(
        {"LAB_LEDGER__PATH": "runs/x.jsonl", "LAB_SECRET_BROKER_TOKEN": "swordfish"}
    )

    assert overrides == {"ledger": {"path": "runs/x.jsonl"}}
    assert "swordfish" not in repr(overrides)


def test_missing_secret_raises() -> None:
    """There is no default, and an empty value is absent.

    An exported-but-empty variable is the usual shape of a misconfigured CI
    secret. Reading it as valid means authenticating with nothing, and a run that
    degrades silently is indistinguishable from one that worked until it reaches
    something real.
    """
    with pytest.raises(MissingSecretError, match="LAB_SECRET_BROKER_TOKEN"):
        get_secret("broker_token", environ={})

    with pytest.raises(MissingSecretError):
        get_secret("broker_token", environ={"LAB_SECRET_BROKER_TOKEN": ""})


def test_get_secret_reads_the_environment_when_present() -> None:
    """The negative control: the boundary permits a genuinely present secret."""
    assert get_secret("broker_token", environ={"LAB_SECRET_BROKER_TOKEN": "swordfish"}) == (
        "swordfish"
    )
