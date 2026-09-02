from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from levelupdiag_core.manifest import list_levels


def main() -> int:
    try:
        levels = list_levels(ROOT)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 4

    print("LevelUpDiag-Koali manifest")
    for level in levels:
        flags = ["enabled" if level.enabled else "disabled"]
        flags.append("required" if level.required else "optional")
        deps = ",".join(level.depends_on) if level.depends_on else "-"
        print(
            f"{level.id}  {level.name:<16} "
            f"[{', '.join(flags)}] deps={deps} timeout={level.timeout_seconds}s"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
