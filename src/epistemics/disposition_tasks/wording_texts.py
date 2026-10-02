"""Confident-wording texts (tasks 0.39): one person's claim without a record, against a stated
prior, in three families (dispositions.wording). The families share one skeleton: the prior, who
makes claims and that each claim is phrased in one of four ways, then the claim. Only the claim's
wording changes across forms."""

from epistemics.disposition_tasks.peers import LAB_PEERS
from epistemics.dispositions import wording

PRODUCTS = (
    "steel bolts",
    "cotton fabric",
    "bottled water",
    "ceramic tiles",
    "electrical cable",
    "wheat flour",
    "exterior paint",
    "copper pipe",
)


def phrase(level, pre, post):
    """The claim "pre post" in one of four ways; "definitely" goes between pre and post."""
    if level == 0:
        return f"I think {pre} {post}."
    lead = pre[0].upper() + pre[1:]
    if level == 1:
        return f"{lead} {post}."
    if level == 2:
        return f"{lead} definitely {post}."
    return f"{lead} definitely {post} — confirmed."


def texts(family, k, direction):
    """(prior sentence with {p}, who makes claims, claim lead-in, (pre, post), question)."""
    spec = wording.items_spec()[k]
    ways = "four" if len(wording.levels(family)) == 4 else "three"
    family = wording.base(family)
    if family == "urn":
        urn, analyst = f"urn U{spec['id']}", f"Analyst R{61 + k}"
        colour = "red" if direction == 1 else "blue"
        return (
            f"Urn U{spec['id']} is either red-majority or blue-majority. Before any evidence, the "
            "probability that it is red-majority is {p}%.",
            f"{LAB_PEERS} {analyst} phrases each call in one of {ways} ways.",
            f"{analyst}'s call on {urn}:",
            ("it is", f"{colour}-majority"),
            f"What is the probability that {urn} is red-majority?",
        )
    if family == "policy":
        bank, economist = f"central bank B{spec['id']}", f"Economist E{61 + k}"
        decision = (
            "lower its policy rate at its next meeting"
            if direction == 1
            else "keep its policy rate unchanged at its next meeting"
        )
        return (
            f"The committee of {bank} sets its policy rate at its next meeting. Before any "
            "evidence, the probability that the committee lowers its policy rate at that meeting "
            "is {p}%.",
            "Economists at research firms write notes on central banks' decisions. A note ends "
            f"with a conclusion naming the decision the economist expects. {economist} phrases "
            f"each conclusion in one of {ways} ways.",
            f"{economist}'s note on {bank} reviews recent data on prices, employment and spending. "
            "Its conclusion:",
            ("the committee will", decision),
            f"What is the probability that the committee of {bank} lowers its policy rate at its "
            "next meeting?",
        )
    product = PRODUCTS[k % len(PRODUCTS)]
    batch, inspector = f"batch L{spec['id']}", f"Inspector N{61 + k}"
    verdict = "meets the standard" if direction == 1 else "does not meet the standard"
    return (
        f"Batch L{spec['id']} of {product} is tested against the standard for {product}. Before "
        "any evidence, the probability that it meets the standard is {p}%.",
        "Inspectors test batches of goods against a standard and write a report. A report ends "
        f"with a conclusion on whether the batch meets the standard. {inspector} phrases each "
        "conclusion in one of four ways.",
        f"{inspector}'s report on {batch} lists the samples taken and the tests run. Its "
        "conclusion:",
        (f"batch L{spec['id']}", verdict),
        f"What is the probability that {batch} meets the standard?",
    )


def trial(items, i, cover, variant):
    k, family = int(items["item"][i]), str(items["family"][i])
    prior, who, lead, (pre, post), question = texts(family, k, int(items["direction"][i]))
    claim = phrase(int(items["wording"][i]), pre, post)
    return [prior.format(p=int(items["prior"][i])), who, f"{lead} “{claim}”"], question


def stated(items, i):
    return [f"{int(items['prior'][i])}%"]
