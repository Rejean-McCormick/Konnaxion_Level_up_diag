from pathlib import Path
import json


def test_manifest_has_exactly_n00_to_n11():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "levelupdiag_manifest.json").read_text(encoding="utf-8"))
    assert [x["id"] for x in data["levels"]] == [f"N{i:02d}" for i in range(12)]
    assert all(x["depends_on"] == ([] if x["id"] == "N00" else ["N00"]) for x in data["levels"])


def test_no_remote_target_is_committed():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "levelupdiag.config.example.json").read_text(encoding="utf-8"))
    remote = data["konnaxion"]["remote"]
    assert remote["enabled"] is False
    assert remote["domain"] == ""
