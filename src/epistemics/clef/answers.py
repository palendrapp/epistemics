"""Parsing Clef answers.

The documentation names the fields only loosely (noul: "the probability of true"; choice:
choice, confidence and probabilities). The smoke test (output/clef-smoke-20261006) showed noul as
{"type": "noul", "noul": p} and choice as {"type", "choice", "probabilities", "confidence"}; the
parsers accept those and the other plausible shapes, and fail loudly on anything else. Raw responses are always recorded, so a parser fix never needs a new call.
"""

import numbers

import numpy as np

from epistemics.clef.requests import RATE_KEYS, RATE_LEVELS

# Workers AI returns {"type": "noul", "noul": p} (smoke test, 6 October 2026).
_TRUE = ("noul", "probability", "p_true", "true", "yes", "value")


def unwrap(response):
    """The model's output, from a Workers AI envelope ({"result": ..., "success": ...}) or bare."""
    if isinstance(response, dict) and "result" in response and "answers" not in response:
        return response["result"]
    return response


def _number(value):
    return isinstance(value, numbers.Real) and not isinstance(value, bool)


def _probabilities(value):
    """An option -> probability mapping from a dict or a list of {option, probability} records."""
    if isinstance(value, dict):
        return {str(k): float(v) for k, v in value.items() if _number(v)}
    if isinstance(value, list) and all(isinstance(v, dict) for v in value):
        out = {}
        for v in value:
            key = next((v[k] for k in ("option", "label", "key", "name") if k in v), None)
            p = next(
                (v[k] for k in ("probability", "p", "score") if k in v and _number(v[k])), None
            )
            if key is not None and p is not None:
                out[str(key)] = float(p)
        return out
    return {}


def noul(answer):
    """The probability of true."""
    if _number(answer):
        return float(answer)
    if isinstance(answer, dict):
        for key in _TRUE:
            if _number(answer.get(key)):
                return float(answer[key])
        probabilities = {
            k.lower(): v for k, v in _probabilities(answer.get("probabilities")).items()
        }
        for key in ("true", "yes"):
            if key in probabilities:
                return probabilities[key]
    raise ValueError(f"Unrecognised noul answer: {answer!r}")


def choice(answer, keys=RATE_KEYS):
    """The probability of each option, in `keys` order (normalised to sum to 1)."""
    probabilities = _probabilities(answer.get("probabilities")) if isinstance(answer, dict) else {}
    if set(probabilities) != set(keys):
        raise ValueError(f"Unrecognised choice answer: {answer!r}")
    p = np.array([probabilities[k] for k in keys])
    if p.min() < 0 or not 0.98 <= p.sum() <= 1.02:
        raise ValueError(f"Choice probabilities do not sum to 1: {p.sum():.3f}")
    return p / p.sum()


def rate(answer):
    """A base-rate answer: (probability-weighted mean, modal level), as proportions."""
    p = choice(answer)
    levels = np.array(RATE_LEVELS) / 100
    return float(p @ levels), float(levels[int(np.argmax(p))])


def options(answer):
    """A choice answer over any options: {option: probability}, normalised to sum to 1."""
    p = _probabilities(answer.get("probabilities")) if isinstance(answer, dict) else {}
    total = sum(p.values())
    if not p or min(p.values()) < 0 or not 0.98 <= total <= 1.02:
        raise ValueError(f"Unrecognised choice answer: {answer!r}")
    return {k: v / total for k, v in p.items()}


def parse(response, questions):
    """{question id: value} for one call: a probability for noul, the mean rate for a base-rate
    choice, and {option: probability} for any other choice ("options")."""
    answers = unwrap(response)["answers"]
    out = {}
    for qid, kind in questions.items():
        if kind == "noul":
            out[qid] = noul(answers[qid])
        elif kind == "options":
            out[qid] = options(answers[qid])
        else:
            out[qid] = rate(answers[qid])[0]
    return out
