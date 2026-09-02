"""Canonical LevelUpDiag-Koali verdicts and aggregation rules."""

from __future__ import annotations

from collections.abc import Iterable

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
SKIP = "SKIP"
BLOCKED = "BLOCKED"
PARTIAL = "PARTIAL"
ERROR = "ERROR"
INFRA_ERROR = "INFRA_ERROR"
CONFIG_ERROR = "CONFIG_ERROR"

VERDICTS: tuple[str, ...] = (
    PASS,
    WARN,
    FAIL,
    SKIP,
    BLOCKED,
    PARTIAL,
    ERROR,
    INFRA_ERROR,
    CONFIG_ERROR,
)

# From least to most severe. The ordering is explicit so aggregation is
# deterministic even where the historical LevelUpDiag implementation treated
# multiple verdicts as equivalent severity classes.
_PRECEDENCE: dict[str, int] = {
    PASS: 0,
    SKIP: 1,
    WARN: 2,
    PARTIAL: 3,
    FAIL: 4,
    BLOCKED: 5,
    INFRA_ERROR: 6,
    CONFIG_ERROR: 7,
    ERROR: 8,
}


def normalize_verdict(value: str) -> str:
    """Return the canonical verdict spelling or reject an unsupported value.

    Whitespace and case are normalized deliberately. Missing or unknown values
    are configuration/programming errors and are never converted to ``PASS``.
    """

    if not isinstance(value, str):
        raise ValueError("verdict must be a string")
    normalized = value.strip().upper()
    if normalized not in _PRECEDENCE:
        raise ValueError(f"unsupported verdict: {value!r}")
    return normalized


def aggregate_verdicts(values: Iterable[str]) -> str:
    """Return the most severe verdict from a non-empty iterable.

    An empty collection has no successful meaning, so it is rejected rather
    than silently becoming ``PASS``.
    """

    normalized = [normalize_verdict(value) for value in values]
    if not normalized:
        raise ValueError("cannot aggregate an empty verdict collection")
    return max(normalized, key=_PRECEDENCE.__getitem__)


def exit_code(verdict: str, *, strict_warn: bool = False) -> int:
    """Map a canonical verdict to the stable process-exit convention."""

    status = normalize_verdict(verdict)
    if status in {PASS, SKIP}:
        return 0
    if status in {WARN, PARTIAL}:
        return 1 if strict_warn else 0
    if status in {FAIL, BLOCKED}:
        return 2
    if status == INFRA_ERROR:
        return 3
    if status == CONFIG_ERROR:
        return 4
    return 5
