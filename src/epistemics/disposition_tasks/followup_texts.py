"""Follow-up texts (tasks 0.35): the peer-advice cases as they are, a first case asking whether
the outcome is likely or unlikely, and the follow-up asking for its probability."""

from epistemics.dispositions import followup

ASK = "What is the probability that "
FIRST = "Is it likely or unlikely that "
PREVIOUS = "The previous case asked about the same urn."


def trial(items, i, cover, variant):
    from epistemics.disposition_tasks.render import RENDERERS, items_for

    base = int(items["base"][i])
    base_variant = followup.VARIANTS[str(items["variant"][i])]
    lines, question = RENDERERS[followup.BASE](items_for(followup.BASE), base, cover, base_variant)
    assert question.startswith(ASK), question
    kind = str(items["kind"][i])
    if kind == "first":
        return lines, FIRST + question[len(ASK) :]
    if kind == "followup":
        return [*lines, PREVIOUS], question
    return lines, question


def stated(items, i):
    from epistemics.disposition_tasks.render import stated_percentages

    base_variant = followup.VARIANTS[str(items["variant"][i])]
    return stated_percentages(followup.BASE, int(items["base"][i]), base_variant)
