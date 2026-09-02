"""Artifact path helpers for LevelUpDiag-Koali."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

_SLUG_SEPARATORS = re.compile(r"[-_\s/\\]+")
_SLUG_UNSAFE = re.compile(r"[^a-z0-9_-]+")


def safe_slug(value: str) -> str:
    """Return a conservative filesystem-safe slug.

    The result contains lowercase ASCII letters, digits and hyphens only and
    can therefore be safely appended to an already trusted runtime root.
    """

    text = str(value).strip().lower()
    text = _SLUG_SEPARATORS.sub("-", text)
    text = _SLUG_UNSAFE.sub("", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "artifact"


def level_artifacts_dir(root: str | Path, level_id: str, level_name: str) -> Path:
    """Create and return the artifact directory owned by one level."""

    base = Path(root).expanduser().resolve()
    directory = (base / safe_slug(f"{level_id}-{level_name}")).resolve()
    if not directory.is_relative_to(base):
        raise ValueError("artifact path escapes the configured root")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def open_path(path: str | Path) -> None:
    """Reveal a local path without executing the artifact itself.

    Directories are opened in the platform file manager.  For files, their
    parent directory is opened (and selected on Windows when possible) rather
    than invoking the file through its association.
    """

    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(target)

    if os.name == "nt":
        if target.is_file():
            subprocess.Popen(["explorer.exe", "/select,", str(target)], shell=False)
        else:
            subprocess.Popen(["explorer.exe", str(target)], shell=False)
        return

    folder = target if target.is_dir() else target.parent
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(folder)], shell=False)
        return

    opener = shutil_which("xdg-open")
    if opener is None:
        raise RuntimeError("No supported file-manager opener is available")
    subprocess.Popen([opener, str(folder)], shell=False)


def shutil_which(name: str) -> str | None:
    """Small indirection kept local so opening paths is easy to test/patch."""

    import shutil

    return shutil.which(name)
