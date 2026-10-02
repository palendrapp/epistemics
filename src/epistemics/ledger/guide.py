"""A first reading guide: the passport in plain language, per configuration.

Each reading is something a user of a configuration could act on, with the evidence behind it,
how much evidence there is, and the conditions it was measured under. The rules that turn numbers
into sentences are fixed here, so the guide regenerates from the ledger and changes only when the
evidence does. Readings describe behaviour in these tasks; reported probabilities are observations,
not access to internal beliefs.
"""

import math

VERSION = "reading-guide/0.7.1"
NAMES = {
    "astra": "GPT-6 Astra",
    "sol": "GPT-6 Sol",
    "astra-low": "GPT-6 Astra, low effort",
    "sol-low": "GPT-6 Sol, low effort",
    "astra-high": "GPT-6 Astra, high effort",
    "sol-high": "GPT-6 Sol, high effort",
    "luna": "GPT-5.6 Luna",
    "terra": "GPT-5.6 Terra",
}
TOPICS = (
    ("base-rates", "What it assumes"),
    ("structures", "Which hidden structures it considers"),
    ("evidence", "How it weighs evidence"),
    ("decisions", "How it values information"),
    ("framing", "How a question's framing changes its numbers"),
    ("reliability", "How far to trust its numbers"),
)
# Frame sensitivity (docs/deliberation-style-design.md): a follow-up changes the readout when the
# share of round answers differs by at least READOUT_SHIFT, and the content when follow-ups sit at
# least CONTENT_SHIFT log-odds further from the configuration's own ladder than its fresh answers.
READOUT_SHIFT = 0.25
CONTENT_SHIFT = 0.25
FRAME_EVIDENCE = (
    "Growth-trend cases asked fresh (as a set of thresholds, or one at a time) and as follow-ups "
    "to another question about the same case; peer-advice cases, open and with the record stated"
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
    "Fictional forecasting cases about company demand, and abstract cases about urns and "
    "sensors, with the numbers stated in the case; one fresh session per context, medium "
    "reasoning effort unless named otherwise."
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
            detail += (
                "; in the prompted dossiers, which named the mechanism and asked for its base "
                f"rate, {pct(row['prompted_irrelevant'])}."
            )
        else:
            detail += "."
        if row.get("named") and row["named"]["range"] >= 0.30:
            claim += (
                " One sentence saying that outlets can copy one another is enough for it to "
                "discount obvious copiers."
                if family == "relay"
                else " One sentence saying that some companies hide bad numbers is enough for it "
                "to read silence as bad news when there is a motive."
            )
        if row.get("named"):
            extreme = "aggregator" if family == "relay" else "bonus description"
            detail += (
                " One added sentence saying the mechanism exists, with no rate, moved the "
                f"{extreme} from {pct(mapping[4])} to {pct(row['named']['mapping'][4])} "
                f"({count(row['named']['sessions'])})."
            )
        if row.get("asked"):
            detail += (
                " Asked for each description's base rate as well, it gave an irrelevant "
                f"description {pct(row['asked']['irrelevant'])} ({count(row['asked']['sessions'])})."
            )
        result.append(
            reading(
                f"noticing-{family}",
                "structures",
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
    carried = [f for f, r in rows if r["gain_over_neutral"] > 0]
    sessions = sum(r["dossier_sessions"] for _, r in rows)
    kinds = {"relay": "news outlets", "disclosure": "company updates"}
    better = len(carried) == len(rows)
    if better:
        claim = (
            "It reads realistic document bundles the way it reads formal cases: what it does "
            f"with formal cases predicts its answers on realistic dossiers to within about "
            f"{max(1, round(100 * worst))} points."
        )
        value = f"within {max(1, round(100 * worst))} points"
    elif carried:
        kept = " and ".join(kinds[f] for f in carried)
        lost = " and ".join(kinds[f] for f, _ in rows if f not in carried)
        claim = (
            f"What it does with formal cases carries over to realistic documents for {kept}, "
            f"but not for {lost}."
        )
        value = f"{kinds[carried[0]]} only" if len(carried) == 1 else "partly"
    else:
        claim = (
            "What it does with formal cases does not predict its answers on realistic documents."
        )
        value = "does not carry over"
    return reading(
        "documents",
        "evidence",
        claim,
        "The same cases, rewritten as news stories, shareholder letters and company profiles with "
        "unrelated documents mixed in.",
        f"Dossier transfer, {count(sessions)}.",
        sessions,
        fact=("Formal readings carry to real documents", value),
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


def v2_cells(v2, trait, config):
    """A configuration's battery v2 cells for one trait, in task order (missing cells dropped)."""
    cells = (((v2 or {}).get("traits") or {}).get(trait) or {}).get("cells") or {}
    return [v for key, v in cells.items() if key.split("/")[0] == config and v is not None]


def v2_transfers(v2, trait):
    """Whether the preregistered leave-one-task-out test found the trait to transfer."""
    r = (((v2 or {}).get("traits") or {}).get(trait) or {}).get("tests") or {}
    task = r.get("task") or {}
    p = task.get("p_holm", task.get("p"))
    return None if task.get("gain") is None else bool(task["gain"] > 0 and p < 0.05)


V2_EVIDENCE = "Battery v2 (preregistered): six abstract tasks, six configurations"


def fidelity_trait(config, v2):
    """Stated-applied fidelity as a tested general trait, when battery v2 found it to transfer."""
    gaps = v2_cells(v2, "stated_applied_gap", config)
    if not gaps or not v2_transfers(v2, "stated_applied_gap"):
        return None
    points = round(100 * float(sum(gaps) / len(gaps)))
    if points >= 10:
        claim = (
            "In every abstract task tested, its forecasts depart from the base rates it states, "
            f"by about {points} points on average. This held from task to task, so expect it in "
            "tasks not tested."
        )
        caution, value = (
            "The base rates it states are not the ones it uses",
            f"off by about {points} points",
        )
    elif points <= 5:
        claim = (
            "In every abstract task tested, its forecasts use the base rates it states (within "
            f"about {max(points, 1)} points). This held from task to task."
        )
        caution, value = None, f"within about {max(points, 1)} points"
    else:
        claim = (
            f"Its forecasts depart somewhat from the base rates it states (about {points} points "
            "on average across the abstract tasks tested)."
        )
        caution, value = None, f"about {points} points apart"
    return reading(
        "fidelity-trait",
        "reliability",
        claim,
        f"Mean gap between stated and applied base rates at the ambiguous levels, over {len(gaps)} "
        "tasks. The preregistered test found that each configuration keeps its position relative "
        "to the others from task to task, including across tasks with different structures.",
        f"{V2_EVIDENCE}.",
        2 * len(gaps),
        caution=caution,
        fact=("Uses the base rates it states (six abstract tasks)", value),
    )


def precision(p, config=None, v2=None):
    taus = [math.exp(x) for x in v2_cells(v2, "precision", config)]
    if taus and v2_transfers(v2, "precision") is False:
        lo, hi = spread_points(min(taus)), spread_points(max(taus))
        span = f"±{lo}" if lo == hi else f"±{lo} to ±{hi}"
        return reading(
            "precision",
            "reliability",
            "How noisy its probabilities are depends mostly on the task, not on the configuration: "
            f"across the abstract tasks tested its noise ranged from {span} points at mid-range.",
            "A preregistered test found no stable ordering of configurations by precision from task "
            "to task, so precision is reported per task, not as a trait.",
            f"{V2_EVIDENCE}; {count(5 * len(taus))}.",
            5 * len(taus),
            {"kind": "spread", "points": hi},
            fact=("Noise in its probabilities", f"{span} points, by task"),
        )
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


CONDITIONS = {
    "corroboration-cues": "formal relay cases",
    "disclosure-cues": "formal disclosure cases",
    "corroboration-dossier": "relay dossiers",
    "disclosure-dossier": "disclosure dossiers",
    "corroboration-asked": "relay dossiers that name copying and ask for its rate",
    "disclosure-asked": "disclosure dossiers that name selective silence and ask for its rate",
    "corroboration-probed": "relay dossiers that name copying, ask for its rate and ask whether "
    "each report was copied",
    "copying-urn-asked": "abstract copying cases that name copying and ask for its rate",
    "copying-urn-probed": "abstract copying cases that also ask whether each reading was copied",
    "selection-urn-asked": "abstract selection cases that name it and ask for its rate",
    "selection-urn-probed": "abstract selection cases that also ask whether each reporter selects",
    "mismatch-urn-asked": "abstract mismatch cases that name it and ask for its rate",
    "mismatch-urn-probed": "abstract mismatch cases that also ask whether each reading was misfiled",
    "echo-urn-asked": "abstract cases with observers who may repeat each other, asked for its rate",
    "echo-urn-probed": "abstract repeating-observer cases that also ask about each report",
    "hub-urn-asked": "abstract cases with hubs that may drop readings, asked for its rate",
    "hub-urn-probed": "abstract dropping-hub cases that also ask about each hub",
    "stale-urn-asked": "abstract cases with readings that may predate a refill, asked for its rate",
    "stale-urn-probed": "abstract stale-reading cases that also ask about each reading",
}


def coherence(p):
    x = p.get("description_coherence")
    if not x:
        return None
    k, n = x
    # A condition is an exception when forecasts departed widely from the stated rates (mean gap
    # of at least 0.15) in at least two of three or more sessions.
    exceptions = [
        (CONDITIONS.get(key.split("/")[0], key), wide, nc)
        for key, (_, nc, wide) in sorted(
            (p.get("description_coherence_by_condition") or {}).items()
        )
        if nc >= 3 and wide >= 2
    ]
    if k >= 0.8 * n and exceptions:
        label, wide, nc = exceptions[0]
        claim = (
            "The base rates it states are usually the ones its forecasts use. In "
            f"{label}, its forecasts departed widely from the rates it stated in {wide} of "
            f"{nc} sessions."
        )
        caution = "Stated and applied base rates sometimes come apart"
    elif k >= 0.8 * n:
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
        if exceptions:
            label, wide, nc = exceptions[0]
            claim += (
                f" In {label}, its forecasts departed widely from the rates it stated in {wide} "
                f"of {nc} sessions."
            )
        caution = None
    return reading(
        "coherence",
        "reliability",
        claim,
        f"In {k} of {n} sessions every stated base rate was within 10 points of the one its "
        "forecasts implied."
        + "".join(
            f" In {label}, forecasts departed widely (by 15 points or more on average) in "
            f"{wide} of {nc} sessions."
            for label, wide, nc in exceptions
        ),
        f"Description modules and prompted dossiers, {count(n)}.",
        n,
        {"kind": "count", "k": k, "n": n},
        caution,
        fact=("Uses the base rates it states", f"{k} of {n} sessions"),
    )


# The prompting a threshold θ stands for, on the salience ladder (a structure is considered about
# half the time at the rung equal to θ).
PROMPTING = (
    (0, "unprompted"),
    (1, "once the structure is named"),
    (2, "once asked for the structure's base rate"),
    (3, "once also asked about each case"),
)
STRUCTURE_NAMES = (
    "copying and selective silence in document dossiers, and copying, selective reporting and "
    "misfiled readings in abstract tasks"
)


def prompting_range(theta):
    """Prompting described for a threshold, as a phrase: "no prompting", "a mention", ..."""
    return (
        "no prompting"
        if theta <= 0
        else "a mention"
        if theta <= 1
        else "a question about how common it is"
        if theta <= 2
        else "a question about each case"
        if theta <= 3
        else "more than every prompt tested"
    )


def prompting(theta):
    for limit, text in PROMPTING:
        if theta <= limit:
            return text
    return "not even when asked about each case"


def carry_over(config, hierarchy, v2=None):
    """Whether noticing one hidden structure predicts noticing another: from battery v2's
    preregistered test when it covers this configuration, otherwise from the hierarchical
    second-layer fit (only a fit that meets its validity rule is read)."""
    thetas = v2_cells(v2, "noticing_threshold", config)
    transfers = v2_transfers(v2, "noticing_threshold")
    if thetas and transfers is not None:
        lo, hi = min(thetas), max(thetas)
        if transfers:
            claim = (
                "How much prompting it needs before it considers a hidden structure keeps its "
                "place relative to other configurations from one structure to another."
            )
            caution, value = None, "Yes"
        else:
            claim = (
                "Whether it considers one hidden structure does not tell you whether it will "
                "consider another: across the abstract tasks tested, it needed anything from "
                f"{prompting_range(lo)} to {prompting_range(hi)}."
            )
            caution, value = (
                "Check each hidden structure that matters for your use on its own",
                "No",
            )
        return reading(
            "noticing-carry-over",
            "structures",
            claim,
            f"Noticing thresholds for {len(thetas)} structures ({lo:.1f} to {hi:.1f} rungs of "
            "prompting). The preregistered test found no stable ordering of configurations from "
            "structure to structure.",
            f"{V2_EVIDENCE}.",
            5 * len(thetas),
            caution=caution,
            fact=("Noticing carries over between structures", value),
        )
    fit = ((hierarchy or {}).get("fits") or {}).get(config)
    if not fit or not fit.get("valid"):
        return None
    n = len(fit["structures"])
    sessions = sum(
        len(v) for x in fit["structures"].values() for v in x["session_fidelity"].values()
    )
    lo, hi = fit["theta_new_structure"]["interval_90"]
    tau = fit["tau_theta"]
    t_lo, t_hi = tau["interval_90"]
    reading_ = fit["spread_reading"]
    if reading_ == "generalises":
        claim = (
            f"How much prompting it needs before it considers a hidden structure is about the "
            f"same for all {n} structures tested, so noticing one predicts noticing another."
        )
        caution, value = None, "Yes"
    else:
        claim = (
            "Whether it considers one hidden structure does not tell you whether it will "
            f"consider another. A structure not tested here might be considered {prompting(lo)}, "
            f"or only {prompting(hi)}."
        )
        caution = "Check each hidden structure that matters for your use on its own"
        value = "No" if reading_ == "structure-specific" else "Not shown"
    detail = (
        f"Across {n} hidden structures ({STRUCTURE_NAMES}), the prompting it needed varied by "
        f"about {tau['mean']:.1f} rungs of a four-rung ladder (90% interval {t_lo:.1f} to "
        f"{t_hi:.1f}): unprompted, named, asked for the base rate, asked about each case."
    )
    return reading(
        "noticing-carry-over",
        "structures",
        claim,
        detail,
        f"Hierarchical fit over {n} structures, {count(sessions)}.",
        sessions,
        caution=caution,
        fact=("Noticing carries over between structures", value),
    )


RUNG_PHRASES = (
    "unprompted",
    "once it was mentioned",
    "once also asked how common it is",
    "once also asked about each case",
)


def structure_checks(config, checks):
    """One reading per valid structure check: the prompt that makes it consider the structure."""
    from epistemics.structure_check import ACTIONS, CATALOGUE

    result = []
    for key, check in sorted(((checks or {}).get("checks") or {}).get(config, {}).items()):
        entry = CATALOGUE.get(key)
        # A check fitted to an older wording of the structure is not read.
        if not entry or not check.get("valid") or check.get("format") != entry["format"]:
            continue
        name, rung = entry["name"], check.get("advice", check["recommended_rung"])
        rated = check.get("rated")
        means = [check["inclusion_by_rung"][str(r)]["mean"] for r in range(4)]
        short, sentence = ACTIONS[rung]
        action = sentence.format(name=name, phrase=entry["phrase"])
        if rung == 0:
            claim = f"It considers {name} without being prompted."
            caution = None
        elif rung == "rate":
            claim = (
                f"Prompting alone does not make it reliably take {name} into account, but when "
                "told how common it is, its forecasts use the rate it is given "
                f"({rated['followed']} of {count(rated['sessions'])})."
            )
            caution = f"Needs to be told the rate of {name}"
        elif rung is None:
            # When asked, it may state a low rate and apply it: considered, but judged rare.
            claim = (
                f"Even when prompted in every way tested, it does not reliably take {name} into "
                "account in its forecasts."
            )
            caution = f"Does not reliably take {name} into account"
        else:
            how_often = (
                f"in only about {pct(means[0])} of cases"
                if means[0] < 0.5
                else f"in about {pct(means[0])} of cases, but not reliably"
            )
            claim = (
                f"Unprompted, it considers {name} {how_often}. "
                f"To make sure it does: {action[0].lower()}{action[1:]}"
            )
            caution = f"{'Misses' if means[0] < 0.5 else 'Sometimes misses'} {name} unless prompted"
        steps = ", ".join(f"{pct(m)} {p}" for m, p in zip(means, RUNG_PHRASES, strict=True))
        detail = (
            f"In {entry['setting']}, when nothing in a case hinted at {name}, it considered it in "
            f"about {steps}. The prompts tested were short sentences naming the structure."
        )
        if rated:
            detail += (
                f" Told how common it is for each kind of source, its forecasts followed the "
                f"stated rates in {rated['followed']} of {count(rated['sessions'])}."
            )
            if rung is None:
                claim += " Telling it how common it is did not fix this."
        if entry.get("known_issue"):
            detail += f" Known issue: {entry['known_issue']}"
            caution = (caution + "; " if caution else "") + "the tested wording was ambiguous"
        result.append(
            reading(
                f"check-{key}",
                "structures",
                claim,
                detail,
                f"Structure check, {count(check['sessions'])} on the salience ladder.",
                check["sessions"],
                caution=caution,
                fact=(f"To make it consider {name}", short),
            )
        )
    return result


def undetermined_checks(config, checks):
    """Catalogued structures without a current check, for a configuration that has some: checks
    that did not converge, and structures not yet checked in their current wording."""
    from epistemics.structure_check import CATALOGUE

    mine = ((checks or {}).get("checks") or {}).get(config, {})
    if not mine:
        return []
    lines = []
    for key, entry in CATALOGUE.items():
        check = mine.get(key)
        if check is None or check.get("format") != entry["format"]:
            lines.append(f"whether it considers {entry['name']} unprompted (not yet checked)")
        elif not check.get("valid"):
            lines.append(
                f"whether it considers {entry['name']} unprompted (its check did not converge)"
            )
    return lines


# Confident wording across kinds of claim (docs/exploration-log.md, idea 28): one claim without a
# record, worded "I think...", plainly, "definitely..." or "definitely... confirmed", in three
# families. In each family a configuration's "definitely... confirmed" weight is above, below or
# like the other configurations' median, by whether its 90% interval excludes 1. Moved more: above
# somewhere and below nowhere; moved less: the reverse; otherwise it depends on the kind of claim.
# CEILING_SHARE: how often answers at 99% or more are mentioned.
CEILING_SHARE = 0.4
CLAIM_KINDS = {
    "urn": ("an analyst's call on an urn", "analysts' calls"),
    "policy": ("an economist's forecast of a central bank's decision", "economists' forecasts"),
    "report": ("an inspector's report on a batch of goods", "inspectors' reports"),
}
WORDING_EVIDENCE = (
    "One claim without a record, worded four ways from \u201cI think\u2026\u201d to "
    "\u201cdefinitely\u2026 confirmed\u201d: an analyst's call on an urn, an economist's forecast "
    "and an inspector's report"
)


def probability_from_even(log_odds):
    return 1 / (1 + math.exp(-log_odds))


def kinds(keys):
    names = [CLAIM_KINDS[k][0] for k in keys]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def moved(v):
    lo, hi = v["interval_90"]
    return "above" if lo > 1 else "below" if hi < 1 else "like"


def phrase_set_note(s):
    """The analyst's-call result with three wordings offered rather than four (idea 30)."""
    if not s:
        return "Whether the analyst result depends on the wordings offered is untested."
    lo, hi = s["shift_interval_90"]
    top = "\u201cdefinitely\u2026 confirmed\u201d"
    if hi < 0:
        own = (
            f"it gives {top} less ({s['shift']:+.2f} log-odds), reading it as the top of the "
            "analyst's range"
        )
    elif lo > 0:
        own = f"it gives {top} more ({s['shift']:+.2f} log-odds)"
    else:
        own = (
            f"its weight on {top} shows no clear change ({s['shift']:+.2f} log-odds, 90% "
            f"interval {lo:.2f} to {hi:.2f})"
        )
    return (
        f"The analyst result depends on the wordings offered: when an analyst uses three wordings "
        f"rather than four, {own}, and such a call moves it {s['three']:.2f} times as far as the "
        f"others, against {s['four']:.2f} with four in the same collection."
    )


def confident_wording(p):
    """How far a confidently worded claim without a record moves it, against the other
    configurations, across kinds of claim."""
    f = p.get("wording_sensitivity")
    if not f or not f.get("families"):
        return None
    fam = {k: f["families"][k] for k in CLAIM_KINDS if k in f["families"]}
    side = {k: moved(v) for k, v in fam.items()}
    above = [k for k in fam if side[k] == "above"]
    below = [k for k in fam if side[k] == "below"]
    like = [k for k in fam if side[k] == "like"]
    pooled = f["pooled_ratio"]

    def scope(keys):
        return "in every kind of claim measured" if len(keys) == len(fam) else f"for {kinds(keys)}"

    def reach(k, phrase):
        return (
            f"{phrase} {CLAIM_KINDS[k][0]}, \u201cdefinitely\u2026 confirmed\u201d takes it from "
            f"50% to about {pct(probability_from_even(fam[k]['confident']))}, "
            f"{fam[k]['ratio']:.1f} times as far as the others."
        )

    if above and not below:
        top = max(above, key=lambda k: fam[k]["ratio"])
        claim = (
            "Without a record, a confidently worded claim moves it further than the other "
            f"configurations {scope(above)}"
            + (f", and about as far for {kinds(like)}" if like else "")
            + ". "
            + reach(top, "On")
        )
        fact = f"Moved more ({pooled:.1f}\u00d7 others)"
    elif below and not above:
        low = min(below, key=lambda k: fam[k]["ratio"])
        claim = (
            "Without a record, a confidently worded claim moves it less than the other "
            f"configurations {scope(below)}"
            + (f", and about as far for {kinds(like)}" if like else "")
            + (", and its answers change least with the wording" if f.get("least_spread") else "")
            + ". "
            + reach(low, "On")
        )
        fact = f"Moved less ({pooled:.1f}\u00d7 others)"
    elif not above and not below:
        claim = (
            "Without a record, a confidently worded claim moves it about as far as the other "
            "configurations in every kind of claim measured."
        )
        fact = "Like the others"
    else:
        claim = (
            "How far confident wording moves it depends on the kind of claim: further than the "
            f"other configurations for {kinds(above)}, less for {kinds(below)}"
            + (f", about as far for {kinds(like)}" if like else "")
            + "."
        )
        fact = f"Depends on the claim ({pooled:.1f}\u00d7)"
    certain = [
        (k, v["ceiling"])
        for k, v in fam.items()
        if v.get("ceiling") is not None and v["ceiling"] >= CEILING_SHARE
    ]
    if certain:
        parts = [f"{share:.0%} of its answers on {CLAIM_KINDS[k][1]}" for k, share in certain]
        claim += (
            " A \u201cdefinitely\u2026 confirmed\u201d claim often takes it to 99% or more ("
            + "; ".join(parts)
            + ")."
        )
    if f.get("record_ratio") is not None and abs(f["record_ratio"] - 1) <= 0.05:
        claim += " Given an analyst's record, it weighs a call exactly as the record implies."
    detail = (
        "Weight of a \u201cdefinitely\u2026 confirmed\u201d claim without a record, in log-odds, "
        "against the median of the other configurations: "
        + "; ".join(
            f"{CLAIM_KINDS[k][1]} {v['confident']:.2f} ({v['ratio']:.2f}\u00d7, 90% interval "
            f"{v['interval_90'][0]:.2f}\u2013{v['interval_90'][1]:.2f}; \u201cI think\u2026\u201d "
            f"{v['tentative']:.2f})"
            for k, v in fam.items()
        )
        + f". Across the three, {pooled:.2f} times the others."
    )
    if f.get("record_ratio") is not None:
        detail += (
            f" With an analyst's record stated: {f['record_ratio']:.2f} of the weight the record "
            "implies."
        )
    return reading(
        "confident-wording",
        "evidence",
        claim,
        detail,
        f"{WORDING_EVIDENCE}; one collection.",
        f["sessions"],
        {
            "kind": "values",
            "values": [probability_from_even(v["confident"]) for v in fam.values()],
            "labels": [CLAIM_KINDS[k][1] for k in fam],
        },
        caution=(
            "Exploratory: one collection, four configurations compared with each other. Answers "
            "at 99% or more understate how far a claim moves it, so ratios there are lower "
            "bounds, and an interval can include 1. " + phrase_set_note(f.get("phrase_sets"))
        ),
        fact=("Confident wording, no record", fact),
    )


def framing(p):
    """Readout against content: does a follow-up change how precisely it reports, or what?"""
    f = p.get("frame_sensitivity")
    if not f or f["fresh"]["share_5"] is None or f["follow_up"]["share_5"] is None:
        return None
    fresh, follow = f["fresh"]["share_5"], f["follow_up"]["share_5"]
    readout = follow - fresh
    content = (
        f["distance_follow_up"] - f["distance_direct"]
        if f.get("distance_follow_up") is not None and f.get("distance_direct") is not None
        else 0.0
    )
    computed = f.get("computed_error")
    exact = computed is not None and max(computed.values()) <= 0.05
    if readout >= READOUT_SHIFT and content < CONTENT_SHIFT:
        claim = (
            "Asked for a probability as a follow-up to another question about the same case, it "
            f"answers in round numbers ({pct(follow)} at multiples of 5, against {pct(fresh)} "
            "asked fresh), but the answers stay where its fresh answers put them."
        )
        fact = f"Rounder ({pct(follow)} against {pct(fresh)}); same answers"
    elif readout <= -READOUT_SHIFT and content < CONTENT_SHIFT:
        claim = (
            f"Its answers are rounder asked fresh ({pct(fresh)} at multiples of 5) than as a "
            f"follow-up to another question about the same case ({pct(follow)}), and stay about "
            "where they were."
        )
        fact = f"Finer as a follow-up ({pct(follow)} against {pct(fresh)})"
    elif content >= CONTENT_SHIFT and abs(readout) < READOUT_SHIFT:
        claim = (
            "Asked as a follow-up to another question about the same case, its probabilities move "
            "away from its fresh answers, though they keep their precision."
        )
        fact = "Same precision; answers move"
    elif content >= CONTENT_SHIFT:
        claim = (
            "Asked as a follow-up to another question about the same case, both the precision "
            "of its probabilities and the probabilities themselves change."
        )
        fact = "Precision and answers change"
    else:
        claim = (
            "Its probabilities keep their precision and stay about where they were whether asked "
            "fresh or as a follow-up to another question about the same case."
        )
        fact = "Unchanged"
    detail = (
        f"Round answers (multiples of 5, mid-range): {pct(fresh)} fresh, {pct(follow)} as "
        f"follow-ups. Distance from its own answers on a ladder of thresholds: "
        f"{f['distance_direct']:.2f} log-odds for fresh single questions, "
        f"{f['distance_follow_up']:.2f} for follow-ups; two follow-up answers to one question "
        f"differ by {f['retest_follow_up']:.2f}."
    )
    if f.get("advice"):
        a = f["advice"]
        detail += (
            f" On open peer-advice cases, {pct(a['fresh'])} round fresh and "
            f"{pct(a['follow_up'])} as follow-ups."
        )
    caution = "Exploratory: one form of each case set, not yet replicated."
    if exact:
        caution += " Answers it can compute exactly were exact either way."
    return reading(
        "framing",
        "framing",
        claim,
        detail,
        f"{FRAME_EVIDENCE}; {count(f['sessions'])}.",
        f["sessions"],
        {
            "kind": "values",
            "values": [fresh, follow],
            "labels": ["round, fresh", "round, follow-up"],
        },
        caution=caution,
        fact=("Asked as a follow-up", fact),
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
            carry_over(
                config,
                (ledger.get("models") or {}).get("hierarchy"),
                (ledger.get("models") or {}).get("battery_v2"),
            ),
            *structure_checks(config, (ledger.get("models") or {}).get("structure_checks")),
            learning(p),
            relative(p),
            reliability(p),
            documents(config, analyses),
            information(p),
            precision(p, config, (ledger.get("models") or {}).get("battery_v2")),
            fidelity_trait(config, (ledger.get("models") or {}).get("battery_v2")),
            sessions_vary(p),
            coherence(p),
            confident_wording(p),
            framing(p),
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
                (
                    "noticing-carry-over",
                    "whether noticing one hidden structure predicts noticing another",
                ),
                ("check-", "which hidden structures it considers, and what prompt makes it"),
                ("learning", "how fast it learns base rates from experience"),
                ("relative", "whether it judges sources relative to each other"),
                ("documents", "whether it behaves the same in realistic documents"),
                ("sessions", "how much its judgements vary between sessions"),
                ("framing", "whether a question's framing changes its numbers"),
                ("confident-wording", "how far confident wording moves it without a record"),
            )
            if not any(m.startswith(key) if key.endswith("-") else m == key for m in measured)
        ] + undetermined_checks(config, (ledger.get("models") or {}).get("structure_checks"))
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
            "The only general trait confirmed so far, stated-applied fidelity, separates model "
            "families (GPT-5.6 against GPT-6), not settings within a family.",
            "Draft: the wording and thresholds are under review.",
        ],
        "configurations": configurations,
    }
