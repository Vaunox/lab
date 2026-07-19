"""Layered configuration, and the secret boundary. Blueprint Part I section 2.

Every parameter lives in versioned config, layered `default.yaml` <- `{env}.yaml`
<- environment variables. `pathlib.Path` throughout, so the code runs identically
in the CI container and on the operator's machine.

**Secrets are environment-only and are never configuration.** `get_secret` reads
the process environment and nothing else -- not a config file, not a default, not
a fallback. A secret with a default is a secret that ships.

One exception, and it is the important one: statutory cost rates, the exchange
calendar, and circuit bands are **not** configuration. They are dated, sourced
data. Presenting a fact as a setting implies it is an opinion, and those are not
opinions.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

ENV_PREFIX = "LAB_"
SECRET_PREFIX = "LAB_SECRET_"

# `LAB_LEDGER__PATH` sets config["ledger"]["path"]. A single underscore is left
# alone because it occurs inside ordinary key names.
NESTING_DELIMITER = "__"

DEFAULT_LAYER = "default"


class ConfigError(RuntimeError):
    """Configuration could not be resolved. Raised at the boundary, never swallowed."""


class MissingSecretError(ConfigError):
    """A required secret is absent from the environment.

    Its own type because the remedy is different in kind: a missing config key is
    a packaging problem, and a missing secret is an operator action. Collapsing
    them into one error invites a caller to handle both with one fallback, and
    the fallback for a secret is the bug.
    """


def _deep_merge(base: dict[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    """Merge `overlay` onto `base`, recursing into nested mappings.

    Nested rather than top-level replacement: a layer that sets one key under
    `ledger` must not silently discard the rest of the `ledger` block. That kind
    of loss is invisible at the call site and shows up as a default reappearing
    three layers later.
    """
    merged = deepcopy(base)
    for key, value in overlay.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, Mapping):
            merged[key] = _deep_merge(existing, value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _read_layer(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} is not valid YAML: {exc}") from exc
    if document is None:
        return {}
    if not isinstance(document, dict):
        raise ConfigError(f"{path} must contain a mapping at the top level")
    return document


def _coerce(raw: str) -> Any:
    """Interpret an environment value using YAML scalar rules.

    So `LAB_LEDGER__ENABLED=true` arrives as a bool and `LAB_LEDGER__RETRIES=3`
    as an int, matching what the same value would mean written in a YAML layer.
    An environment override that changed a setting's *type* would otherwise be a
    silent behaviour change at the bottom of the stack.
    """
    try:
        value = yaml.safe_load(raw)
    except yaml.YAMLError:
        return raw
    return raw if value is None else value


def environment_overrides(environ: Mapping[str, str]) -> dict[str, Any]:
    """Build the environment layer from `LAB_`-prefixed variables.

    `LAB_SECRET_*` is deliberately excluded. Secrets do not enter the config
    object at all, because anything in the config object is a candidate for
    being logged, serialised into a run record, or printed in a traceback.
    """
    overrides: dict[str, Any] = {}
    for name, raw in environ.items():
        if not name.startswith(ENV_PREFIX) or name.startswith(SECRET_PREFIX):
            continue
        path = name[len(ENV_PREFIX) :].lower().split(NESTING_DELIMITER)
        cursor = overrides
        for part in path[:-1]:
            nested = cursor.setdefault(part, {})
            if not isinstance(nested, dict):
                raise ConfigError(f"{name}: {part!r} is both a value and a section")
            cursor = nested
        cursor[path[-1]] = _coerce(raw)
    return overrides


def load_config(
    env: str | None = None,
    config_dir: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Resolve configuration from the layered sources. Blueprint section 2.

    Precedence, lowest to highest: `default.yaml`, then `{env}.yaml`, then
    `LAB_`-prefixed environment variables. Later layers override earlier ones key
    by key rather than wholesale.

    An absent layer contributes nothing and is not an error -- `default.yaml` is
    the floor, and an environment that adds no overrides is the common case. An
    unparseable layer *is* an error: failing loudly at the boundary is the point.
    """
    environ = os.environ if environ is None else environ
    config_dir = Path("config") if config_dir is None else config_dir
    env = environ.get(f"{ENV_PREFIX}ENV", DEFAULT_LAYER) if env is None else env

    resolved = _read_layer(config_dir / f"{DEFAULT_LAYER}.yaml")
    if env != DEFAULT_LAYER:
        resolved = _deep_merge(resolved, _read_layer(config_dir / f"{env}.yaml"))
    return _deep_merge(resolved, environment_overrides(environ))


def get_secret(name: str, environ: Mapping[str, str] | None = None) -> str:
    """Read a secret from the environment. There is no other source.

    Raises `MissingSecretError` when the variable is absent or empty. There is
    deliberately no `default` parameter: a default turns a missing credential
    into a silently degraded run, and the whole reason secrets are environment-
    only is that a degraded run is indistinguishable from a working one until it
    reaches something real.

    An empty string is treated as absent. An exported-but-empty variable is the
    usual shape of a misconfigured CI secret, and reading it as a valid value
    means authenticating with nothing.
    """
    environ = os.environ if environ is None else environ
    variable = f"{SECRET_PREFIX}{name.upper()}"
    value = environ.get(variable, "")
    if not value:
        raise MissingSecretError(
            f"{variable} is not set. Secrets are read from the environment only "
            "-- never from config, never from code, and never with a default"
        )
    return value
