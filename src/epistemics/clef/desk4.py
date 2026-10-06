"""The second confirmation desk (docs/clef-desk4-preregistration.md): the passport mitigation
with its remark classifier calibrated on the desk's labelled past remarks, on fresh meetings.

The robustness world of epistemics.clef.desk2 on new seeds:
  record  40 past meetings: the speakers' scorecard (shown to every lane, weights for the
          passport lane) and the labelled remarks on which the passport lane calibrates the
          model's classifier (the desk knows each past remark's direction)
  pool    100 past meetings of the model's own beliefs, for generic recalibration
  test    1,000 held-out meetings
"""

from epistemics.clef import desk, desk2
from epistemics.clef.requests import MODELS, digest

VERSION = "clef-desk4/0.1.0"
SEEDS = {"record": 20261020, "pool": 20261021, "test": 20261022}
COUNTS = {"record": 40, "pool": 100, "test": 1000}
K_VALUES = (5, 10, 20, 40, 100)
PRIMARY_K = 10
DRAWS = 20
DRAW_SEED = 20261023
PER_MEETING = desk2.PER_MEETING


def meetings(kind):
    return desk2.generate(SEEDS[kind], COUNTS[kind], kind)


def scorecard():
    return desk2.scorecard(meetings("record"))


def record_remarks():
    """[((speaker, text), sign)] for every distinct remark of the record meetings, sorted."""
    return sorted(
        {
            (r["speaker"], r["text"]): r["sign"] for m in meetings("record") for r in m["remarks"]
        }.items()
    )


def items_digest():
    return digest({k: meetings(k) for k in SEEDS} | {"reliability": desk2.RELIABILITY,
                  "echoers": desk2.ECHOERS, "echo": desk2.ECHO})  # fmt: skip


def calls(models=tuple(MODELS)):
    card = scorecard()
    pool, test = meetings("pool"), meetings("test")
    uniq = desk2.unique_remarks(test)
    out = []

    def add(model, part, key, state, questions):
        kinds = {
            k: ("options" if q["type"] == "choice" else q["type"]) for k, q in questions.items()
        }
        meta = {"model": model, "part": part, "key": key, "questions": kinds}
        out.append(
            (
                f"{model}/{part}/{key}",
                meta,
                {"model": model, "state": state, "questions": questions},
            )
        )

    for model in models:
        for i, (key, _) in enumerate(record_remarks()):
            add(model, "record-classify", str(i), *desk.classify_text(*key))
        for m in pool:
            for t in range(PER_MEETING + 1):
                add(model, "pool-belief", f"{m['meeting']}/{t}", desk2.state_text(m, t, card),
                    desk.belief_question())  # fmt: skip
        for m in test:
            for t in range(PER_MEETING + 1):
                key = f"{m['meeting']}/{t}"
                add(model, "choice", key, desk2.state_text(m, t, card), desk.choice_question())
                add(model, "belief", key, desk2.state_text(m, t, card), desk.belief_question())
        for (speaker, text), i in uniq.items():
            add(model, "classify", str(i), *desk.classify_text(speaker, text))
    return out
