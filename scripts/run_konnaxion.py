from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from levelupdiag_core.config import load_config
from levelupdiag_core import runner
from levelupdiag_core.verdicts import exit_code

CAMPAIGNS = {
    "source-audit": ["N00", "N01", "N04", "N11"],
    "auth-debug": ["N00", "N02", "N03", "N04", "N05", "N11"],
    "full-local": ["N00", "N01", "N02", "N03", "N04", "N05", "N06", "N07", "N10", "N11"],
    "connection-debug": ["N00", "N01", "N02", "N03", "N04", "N05", "N06", "N11"],
    "backend": ["N00", "N01", "N02", "N04", "N06", "N11"],
    "frontend": ["N00", "N01", "N03", "N04", "N05", "N11"],
    "local-runtime": ["N00", "N02", "N03", "N04", "N05", "N06", "N11"],
    "capsule-local": ["N00", "N07", "N08", "N11"],
    "deployed": ["N00", "N07", "N08", "N09", "N11"],
    "deep": ["N00", "N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08", "N10", "N11"],
    "full": [f"N{i:02d}" for i in range(12)],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Konnaxion Mega Diagnostic Pack campaigns")
    parser.add_argument("campaign", choices=CAMPAIGNS)
    args = parser.parse_args()
    cfg = load_config(root=ROOT)
    result = runner.run_campaign(args.campaign, CAMPAIGNS[args.campaign], cfg)
    print(f"campaign {result.campaign}: {result.verdict}")
    for item in result.levels:
        print(f"  {item.level} — {item.name}: {item.verdict}")
        for finding in item.findings:
            if finding.severity not in {"PASS", "SKIP"}:
                print(f"      {finding.severity}: {finding.id}: {finding.message}")
    return exit_code(result.verdict)


if __name__ == "__main__":
    raise SystemExit(main())
