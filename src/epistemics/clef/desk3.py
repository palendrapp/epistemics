"""The confirmation desk (docs/clef-desk3-preregistration.md): the robustness world of
epistemics.clef.desk2 on fresh meetings, with the two kinds of history separated.

  record  40 past meetings: the speakers' scorecard (domain facts), fixed, shown to every lane
          (inside the model's prompts too) and used by the passport lane for its weights
  pool    100 past meetings on which the model's own beliefs are collected: its own forecast
          record, from which generic recalibration is fitted on k of them (k = 5 to 100)
  test    400 held-out meetings

The passport lane needs only the domain record; generic recalibration also needs the model's own
forecast record. Same speakers, reliabilities, echoes and remark pools as desk2.
"""

from epistemics.clef import desk, desk2
from epistemics.clef.requests import MODELS, digest

VERSION = "clef-desk3/0.1.0"
SEEDS = {"record": 20261010, "pool": 20261011, "test": 20261012}
COUNTS = {"record": 40, "pool": 100, "test": 400}
K_VALUES = (5, 10, 20, 40, 100)
PRIMARY_K = 10
DRAWS = 20
DRAW_SEED = 20261013
PER_MEETING = desk2.PER_MEETING


def meetings(kind):
    return desk2.generate(SEEDS[kind], COUNTS[kind], kind)


def scorecard():
    return desk2.scorecard(meetings("record"))


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


def record_remarks():
    """{(speaker, text): sign} for every remark in the record meetings (the desk knows their
    directions; that is what its scorecard is built from)."""
    return {(r["speaker"], r["text"]): r["sign"] for m in meetings("record") for r in m["remarks"]}


def record_digest():
    return digest(sorted([list(k) + [v] for k, v in record_remarks().items()]))


def record_calls(models=tuple(MODELS)):
    """Exploratory supplement (docs/clef-desk3-preregistration.md, "Exploratory"): the model's
    classification of every record remark, to calibrate its classifier on labelled domain
    remarks."""
    out = []
    for model in models:
        for i, key in enumerate(sorted(record_remarks())):
            state, questions = desk.classify_text(*key)
            meta = {
                "model": model,
                "part": "record-classify",
                "key": str(i),
                "questions": {"answer": "noul"},
            }
            out.append(
                (
                    f"{model}/record-classify/{i}",
                    meta,
                    {"model": model, "state": state, "questions": questions},
                )
            )
    return out
