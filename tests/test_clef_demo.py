"""The Clef demo in replay mode reproduces the ledger's numbers (offline; skipped when the
recorded roots are not present, since output/ is not in Git)."""

import json
from pathlib import Path

import pytest

from epistemics.clef import demo

ROOTS_PRESENT = all((Path(r) / "calls.jsonl").exists() for r in demo.ROOTS.values())


@pytest.mark.skipif(not ROOTS_PRESENT, reason="recorded Clef roots not present")
def test_replay_matches_the_ledger():
    from epistemics.ledger import clef_battery, clef_desk, clef_far

    answers = demo.Answers(live=False)
    battery = clef_battery.summary(demo.ROOTS["battery"])
    urn = {m: v["bookbag"]["urn"] for m, v in battery["models"].items()}
    far = clef_far.summary(demo.ROOTS["far"], urn)
    desk = clef_desk.summary(demo.ROOTS["desk"])
    for model in ("clef", "clef-flash"):
        events = []
        demo.act1(model, answers, events.append, lambda *_: None)
        passport = next(e for e in events if e["type"] == "passport")
        assert passport["compression"] == pytest.approx(urn[model]["unanimous"]["ratio_5_to_1"])
        events = []
        demo.act2(model, answers, events.append, lambda *_: None)
        ratio5 = next(e for e in events if e["type"] == "far_weight" and e["n"] == 5)["ratio"]
        assert ratio5 == pytest.approx(far["models"][model]["sample_size"]["ratio_5_to_1"])
        events = []
        demo.act3(model, answers, events.append, lambda *_: None, episodes=60)
        cum = next(e for e in events if e["type"] == "summary")["cumulative"]
        for lane, v in desk["models"][model]["lanes"].items():
            assert cum[lane] / 60 == pytest.approx(v["pnl"])
        json.dumps(events, default=float)
