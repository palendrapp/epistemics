"""A first reading guide: the passport in plain language, per configuration.

Each reading is something a user of a configuration could act on, with the evidence behind it,
how much evidence there is, and the conditions it was measured under. The rules that turn numbers
into sentences are fixed here, so the guide regenerates from the ledger and changes only when the
evidence does. Readings describe behaviour in these tasks; reported probabilities are observations,
not access to internal beliefs.
"""

import math

VERSION = "reading-guide/0.1.0"
NAMES = {
    "astra": "GPT-6 Astra",
    "sol": "GPT-6 Sol",
    "astra-low": "GPT-6 Astra, low effort",
    "sol-low": "GPT-6 Sol, low effort",
    "luna": "GPT-5.6 Luna",
    "terra": "GPT-5.6 Terra",
}
TOPICS = (
    ("base-rates", "What it assumes"),
    ("evidence", "How it weighs evidence"),
    ("decisions", "How it values information"),
    ("reliability", "How far to trust its numbers"),
)
# Short forms of the set-A descriptions, strongly reassuring to strongly suggestive.
SHORT = {
    "relay": (
        "twenty reporters interview customers",
        "sometimes runs its own surveys",
        "based in a city on the coast",
        "small newsletter, two analysts",
        "aggregator with no reporters",
    ),
    "disclosure": (
        "checked by an independent auditor",
        "reputation for complete reporting",
        "moved its headquarters",
        "hoping to raise financing",
        "chief executive's bonus depends on it",
    ),
}
MEASURED_IN = (
    "Fictional forecasting cases about company demand, with the numbers stated in the case; "
    "one fresh session per context, medium reasoning effort unless named otherwise."
)


def pct(p):
    return f"{round(100 * p)}%"


def spread_points(tau):
    """One report standard deviation at 50%, in percentage points."""
    return max(1, round(100 * (1 / (1 + math.exp(-tau)) - 0.5)))


def points_text(n):
    return f"±{n} point{'' if n == 1 else 's'}"


def count(n):
    return f"{n} session{'' if n == 1 else 's'}"


def amount(sessions):
    return "several sessions" if sessions >= 3 else "one or two sessions"


def reading(key, topic, claim, detail, evidence, sessions, figure=None, caution=None, fact=None):
    return {
        "key": key,
        "fact": {"label": fact[0], "value": fact[1]} if fact else None,
        "topic": topic,
        "claim": claim,
        "detail": detail,
        "evidence": evidence,
        "sessions": sessions,
        "strength": amount(sessions),
        "figure": figure,
        "caution": caution,
    }


def defaults(p):
    r, s = p.get("relay_default"), p.get("silence_default")
    if not r or not s:
        return None
    sessions = min(r["contexts"], s["contexts"])
    if abs(r["mean"] - 0.5) <= 0.05 and abs(s["mean"] - 0.5) <= 0.05:
        claim = "When a case names a possibility but not how common it is, it treats it as 50/50."
    else:
        claim = (
            "When a case names a possibility but not how common it is, it assumes about "
            f"{pct(r['mean'])} for a copied report and {pct(s['mean'])} for selective silence."
        )
    return reading(
        "defaults",
        "base-rates",
        claim,
        "Told that some outlets copy one another, but not how many, it assumed "
        f"{pct(r['mean'])} that a matching second report was a copy. Told that some companies "
        f"hide bad indicators, it assumed {pct(s['mean'])} that a company's silence was selective.",
        f"Relay defaults, {count(r['contexts'])}; silence defaults, {count(s['contexts'])}.",
        sessions,
        {"kind": "values", "values": [r["mean"], s["mean"]], "labels": ["copied", "selective"]},
        fact=(
            "Base rate when none is given",
            "50/50"
            if claim.endswith("50/50.")
            else f"{pct(r['mean'])} copied, {pct(s['mean'])} selective",
        ),
    )


def descriptions(p, family, sentences):
    mapping = (p.get(f"{family}_description_mapping") or {}).get("cues-a")
    if not mapping:
        return None
    sessions = p[f"{family}_description_sessions"]["cues-a"]
    low, middle, high = mapping[0], mapping[2], mapping[4]
    if family == "relay":
        claim = (
            "Told that some outlets copy others, it turns what it is told about an outlet into a "
            f"base rate for copying: {pct(high)} for an aggregator with no reporters, {pct(low)} "
            "for a newsroom whose reporters interview customers."
        )
        subject = "a report was copied"
    else:
        claim = (
            "Told that some companies hide bad numbers, it turns what it is told about a company "
            f"into a base rate for selective silence: {pct(high)} when the chief executive's bonus "
            f"depends on the numbers, {pct(low)} when an independent auditor checks them."
        )
        subject = "a company's silence was selective"
    irrelevant = sentences[family]["cues-a"][2]
    return reading(
        f"descriptions-{family}",
        "base-rates",
        claim,
        f"The chance it gave that {subject}, for each of five descriptions. An irrelevant detail "
        f"(“{irrelevant}”) left it at {pct(middle)}.",
        f"Formal description modules, set A, {count(sessions)}.",
        sessions,
        {
            "kind": "ladder",
            "values": mapping,
            "labels": list(SHORT[family]),
            "sentences": sentences[family]["cues-a"],
        },
        fact=(
            "When told: copying, newsroom → aggregator"
            if family == "relay"
            else "When told: silence, audited → bonus at stake",
            f"{pct(low)} → {pct(high)}",
        ),
    )


def noticing(config, analyses):
    rows = {
        family: analyses.get("noticing", {}).get(f"{config}/{family}")
        for family in ("relay", "disclosure")
    }
    if not any(rows.values()):
        return []
    result = []
    for family, row in rows.items():
        if not row:
            continue
        mapping = row["unprompted_mapping"]
        spread = mapping[4] - mapping[0]
        what = "copied" if family == "relay" else "selectively silent"
        if max(mapping) <= 0.10:
            claim = (
                "Unless a case says that outlets can copy one another, it treats every report as "
                "independent, even from an aggregator with no reporters."
                if family == "relay"
                else "Unless a case says that companies can hide bad numbers, it reads silence as "
                "uninformative, even when the chief executive's bonus depends on the numbers."
            )
        elif spread >= 0.30:
            claim = (
                "Without being told that outlets copy one another, it still discounts a report "
                f"from a source that looks like a copier ({pct(mapping[4])} for an aggregator "
                "with no reporters)."
                if family == "relay"
                else "Without being told that companies hide bad numbers, it still reads silence "
                "as bad news when the description gives a motive "
                f"({pct(mapping[4])} when the chief executive's bonus depends on it)."
            )
        else:
            claim = (
                "Without being told that outlets copy one another, it only partly considers it "
                f"(at most {pct(max(mapping))} for any outlet)."
                if family == "relay"
                else "Without being told that companies hide bad numbers, it only partly reads "
                f"silence as bad news (at most {pct(max(mapping))})."
            )
        detail = (
            f"In dossiers that never mention the mechanism, the chance it acted on that the "
            f"source was {what}, for each description. An irrelevant detail gave {pct(mapping[2])}"
        )
        if "prompted_mapping" in row:
            detail += f"; when the mechanism was named, {pct(row['prompted_irrelevant'])}."
        else:
            detail += "."
        result.append(
            reading(
                f"noticing-{family}",
                "base-rates",
                claim,
                detail,
                f"Unprompted dossiers, {count(row['unprompted_sessions'])}.",
                row["unprompted_sessions"],
                {
                    "kind": "ladder",
                    "values": mapping,
                    "labels": list(SHORT[family]),
                    "compare": row.get("prompted_mapping"),
                },
                fact=(
                    "Not told: copying, newsroom → aggregator"
                    if family == "relay"
                    else "Not told: silence, audited → bonus at stake",
                    f"{pct(mapping[0])} → {pct(mapping[4])}",
                ),
            )
        )
    return result


def learning(p):
    x = p.get("learning")
    if not x:
        return None
    strength = x["strength_median"]
    return reading(
        "learning",
        "base-rates",
        "Shown how earlier cases turned out, it updates its base rates quickly, as if its "
        f"starting guess were worth about {round(strength)} example{'s' if round(strength) != 1 else ''}.",
        f"It started from {pct(x['start']['mean'])} and moved toward the revealed rate case by "
        f"case; learning was detected in {x['detected']} of {x['contexts']} sessions.",
        f"Learning variants, {count(x['contexts'])}.",
        x["contexts"],
        fact=("Starting guess worth", f"{round(strength)} examples"),
    )


def relative(p):
    c = p.get("relative_judgement_contrast")
    if c is None:
        return None
    sessions = p.get("relative_judgement_sessions") or 0
    if abs(c) <= 0.05:
        claim = (
            "It judges each source on its own description, not against the other sources in view."
        )
    else:
        claim = (
            "Its judgement of a source shifts with the other sources in view, by about "
            f"{round(100 * abs(c))} points."
        )
    return reading(
        "relative",
        "base-rates",
        claim,
        "The same five outlets were judged after three reassuring or three suspicious outlets; "
        f"their priors differed by {round(100 * c):+d} points on average.",
        f"Relative-judgement module, {count(sessions)}.",
        sessions,
        fact=(
            "Judges sources",
            "one at a time" if abs(c) <= 0.05 else "against each other",
        ),
    )


def reliability(p):
    g = p.get("evidence_sensitivity")
    if not g:
        return None
    read = 1 / (1 + math.exp(-g["mean"] * math.log(0.8 / 0.2)))
    if abs(g["mean"] - 1) <= 0.05:
        claim = "It takes stated source reliability at face value."
    elif g["mean"] < 1:
        claim = f"It discounts stated source reliability: a source said to be right 80% of the time counts as about {pct(read)}."
    else:
        claim = f"It overweights stated source reliability: a source said to be right 80% of the time counts as about {pct(read)}."
    return reading(
        "reliability",
        "evidence",
        claim,
        "A source said to be right 80% of the time moves its forecast as much as a source that "
        f"is right {pct(read)} of the time.",
        f"Relay and disclosure modules, {count(g['contexts'])}.",
        g["contexts"],
        fact=("A source stated 80% right counts as", pct(read)),
    )


def documents(config, analyses):
    rows = [
        (family, analyses.get("transfer", {}).get(f"{config}/{family}"))
        for family in ("relay", "disclosure")
    ]
    rows = [(f, r) for f, r in rows if r]
    if not rows:
        return None
    worst = max(r["prediction_mae"]["own_formal"] for _, r in rows)
    better = all(r["gain_over_neutral"] > 0 for _, r in rows)
    sessions = sum(r["dossier_sessions"] for _, r in rows)
    if better:
        claim = (
            "It reads realistic document bundles the way it reads formal cases: what it does "
            f"with formal cases predicts its answers on realistic dossiers to within about "
            f"{max(1, round(100 * worst))} points."
        )
    else:
        claim = "Its answers on realistic dossiers depart from its formal cases."
    return reading(
        "documents",
        "evidence",
        claim,
        "The same cases, rewritten as news stories, shareholder letters and company profiles with "
        "unrelated documents mixed in.",
        f"Dossier transfer, {count(sessions)}.",
        sessions,
        fact=(
            "Realistic documents vs formal cases",
            f"within {max(1, round(100 * worst))} points" if better else "differ",
        ),
    )


def information(p):
    x = p.get("checks_priced_at_decision_value")
    if not x:
        return None
    k, n = x
    if k == n:
        claim = (
            "It values a check only for the decisions the check could change, and pays nothing "
            "for reassurance alone."
        )
    elif k >= 0.9 * n:
        claim = "It almost always values a check only for the decisions it could change."
    else:
        claim = "It sometimes pays for checks beyond what they could change in a decision."
    return reading(
        "information",
        "decisions",
        claim,
        f"It bid exactly the check's decision value in {k} of {n} offers.",
        f"Check-pricing module, {count(n // 24)}.",
        n // 24,
        fact=("Checks priced at decision value", f"{k} of {n}"),
    )


def precision(p):
    tau = p.get("report_noise_median")
    if tau is None:
        return None
    sessions = p["evidence_sensitivity"]["contexts"]
    points = spread_points(tau)
    if points <= 2:
        claim = "Its probabilities are precise: the same evidence gets the same answer to within a point or two."
    else:
        claim = (
            f"Its probabilities carry about ±{points} points of noise at mid-range; treat smaller "
            "differences between its answers as noise."
        )
    return reading(
        "precision",
        "reliability",
        claim,
        f"Median report noise of {tau:.2f} on the log-odds scale, which is {points_text(points)} "
        "around 50%.",
        f"Relay and disclosure modules, {count(sessions)}.",
        sessions,
        {"kind": "spread", "points": points},
        fact=("Noise in its probabilities", points_text(points)),
    )


def sessions_vary(p):
    v = p.get("ambiguous_description_session_sd")
    if not v:
        return None
    points = round(100 * v["estimate"])
    low, high = (round(100 * x) for x in v["interval_95"])
    if high - low > 10:
        claim = (
            "How much its reading of an ambiguous source changes between sessions is not yet "
            f"pinned down: anywhere from ±{low} to ±{high} points."
        )
    else:
        claim = (
            "Its reading of an ambiguous source changes from one session to the next by about "
            f"{points_text(points)}."
        )
    return reading(
        "sessions",
        "reliability",
        claim,
        "Between-session standard deviation of the priors it gave three ambiguous descriptions, "
        f"estimated at {points} points (95% interval {low} to {high}). Clear-cut descriptions "
        "barely move.",
        f"Between-session variance, {count(v['sessions'])}.",
        v["sessions"],
        {"kind": "spread", "points": points, "range": [low, high]},
        fact=(
            "Drift between sessions",
            f"±{low}–{high} points" if high - low > 10 else points_text(points),
        ),
    )


def coherence(p):
    x = p.get("description_coherence")
    if not x:
        return None
    k, n = x
    if k >= 0.8 * n:
        claim = "The base rates it states are the ones its forecasts use."
        caution = None
    elif k <= 0.4 * n:
        claim = (
            "It states sensible base rates, but its forecasts often use different ones. Rely on "
            "its forecasts, not on the assumptions it says it makes."
        )
        caution = "Stated and applied base rates disagree"
    else:
        claim = "The base rates it states and the ones its forecasts use agree in most sessions, not all."
        caution = None
    return reading(
        "coherence",
        "reliability",
        claim,
        f"In {k} of {n} sessions every stated base rate was within 10 points of the one its "
        "forecasts implied.",
        f"Description modules, {count(n)}.",
        n,
        {"kind": "count", "k": k, "n": n},
        caution,
        fact=("Uses the base rates it states", f"{k} of {n} sessions"),
    )


def guide(ledger, descriptors):
    """Readings per configuration from a built ledger (passport and analyses)."""
    analyses = ledger.get("analyses", {})
    configurations = {}
    for config, p in ledger["passport"].items():
        readings = [
            defaults(p),
            descriptions(p, "relay", descriptors),
            descriptions(p, "disclosure", descriptors),
            *noticing(config, analyses),
            learning(p),
            relative(p),
            reliability(p),
            documents(config, analyses),
            information(p),
            precision(p),
            sessions_vary(p),
            coherence(p),
        ]
        readings = [r for r in readings if r]
        measured = {r["key"] for r in readings}
        missing = [
            text
            for key, text in (
                ("defaults", "what it assumes when a base rate is missing"),
                ("descriptions-relay", "how descriptions of outlets set its priors"),
                ("descriptions-disclosure", "how descriptions of companies set its priors"),
                ("noticing-relay", "whether it considers copying unprompted"),
                ("noticing-disclosure", "whether it reads silence as bad news unprompted"),
                ("learning", "how fast it learns base rates from experience"),
                ("relative", "whether it judges sources relative to each other"),
                ("documents", "whether it behaves the same in realistic documents"),
                ("sessions", "how much its judgements vary between sessions"),
            )
            if key not in measured
        ]
        configurations[config] = {
            "name": NAMES.get(config, config),
            "sessions": p["contexts"],
            "readings": readings,
            "not_yet_measured": missing,
        }
    return {
        "schema_version": "epistemics.reading-guide.v1",
        "guide_version": VERSION,
        "repository_commit": ledger.get("repository_commit"),
        "topics": [{"key": k, "title": t} for k, t in TOPICS],
        "measured_in": MEASURED_IN,
        "cautions": [
            "These readings describe what each configuration did in these tasks. They are not "
            "access to its internal beliefs, and they may not hold in other tasks or wordings.",
            "A configuration is a requested model name and reasoning effort. The model behind "
            "the name is not verified and can change.",
            "Numbers come from small numbers of fresh sessions. The evidence line on each reading "
            "says how many.",
            "Draft: the wording and thresholds are under review.",
        ],
        "configurations": configurations,
    }
