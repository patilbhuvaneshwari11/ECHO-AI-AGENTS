import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.loader import load_data
from engine.simulator import run_checks, simulate


def test_planted_problems_are_found():
    rooms, exams, enroll, dist = load_data()
    res = run_checks(exams, rooms, enroll, dist)
    assert len({c["student"] for c in res["clash"]}) == 4  # planted clashes
    assert [o["exam"] for o in res["overload"]] == ["E08"]  # planted overload
    assert res["double_booking"] == []
    assert res["travel"] == []


def test_demo_decision():
    decision = {"action": "relocate", "source_block": "B", "destination_block": "C", "exam_ids": []}
    out = simulate(decision)
    keep, proposed, safer = out["options"]
    assert proposed["risk"]["counts"]["double_booking"] == 1
    assert proposed["risk"]["counts"]["travel"] == 40
    assert proposed["risk"]["score"] > keep["risk"]["score"]
    assert safer["risk"]["score"] <= keep["risk"]["score"]
    assert out["recommended"] == 2
    