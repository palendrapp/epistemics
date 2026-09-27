import argparse
import json
from pathlib import Path

from epistemics.research_world.extract import audit
from epistemics.research_world.render import render
from epistemics.research_world.world import PAIRS, generate, naive_logit, normative_logit, sigmoid
from epistemics.source_learning.storage import encoded, save


def show(seed, family):
    worlds = generate(seed, family)
    dossiers = {p: render(w) for p, w in worlds.items()}
    audit(worlds, dossiers)
    lines = []
    for presentation, world in worlds.items():
        d = dossiers[presentation]
        lines += [
            f"## {family} / {presentation}",
            "",
            f"_Private ledger: normative {sigmoid(normative_logit(world)):.3f}, "
            f"naive {sigmoid(naive_logit(world)):.3f}, demand "
            f"{'strong' if world.strong else 'weak'}._",
            "",
            *d["case"].splitlines(),
            "",
        ]
        for doc in d["documents"]:
            lines.append(f"**{doc['doc_id']} · {doc['kind']} · {doc['source']} · {doc['date']}**  ")
            lines += [doc["text"], ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Research-world generator (development only)")
    sub = parser.add_subparsers(dest="command", required=True)
    sample = sub.add_parser("sample")
    sample.add_argument("--seed", type=int, required=True)
    sample.add_argument("--family", choices=sorted(PAIRS), required=True)
    check = sub.add_parser("audit")
    check.add_argument("--seeds", type=int, default=500)
    precision = sub.add_parser("precision")
    precision.add_argument("--output", type=Path, required=True)
    precision.add_argument("--seed", type=int, default=0)
    precision.add_argument("--repetitions", type=int, default=400)
    a = parser.parse_args()
    if a.command == "sample":
        print(show(a.seed, a.family))
    elif a.command == "audit":
        for seed in range(a.seeds):
            for family in PAIRS:
                worlds = generate(seed, family)
                audit(worlds, {p: render(w) for p, w in worlds.items()})
        print(json.dumps({"audited_pairs": a.seeds * len(PAIRS), "passed": True}))
    else:
        from epistemics.research_world.synthetic import precision as run

        result = run(seed=a.seed, reps=a.repetitions)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        save(a.output, encoded(result))
        print(json.dumps({"rows": len(result["results"])}))


if __name__ == "__main__":
    main()
