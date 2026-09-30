"""Multi-agent battery, Stage 1 (model 0.11, design 0.13): scripted peers
(docs/multi-agent-design.md).

Every case concerns one urn, red-majority or blue-majority with a stated prior. The respondent may
have its own reading, and other lab analysts send calls ("It is red-majority"). Reports are
probabilities that the urn is red-majority, fitted on the log-odds scale with whole-percentage
binning, as for the single-agent modules.

T1 advice: one analyst's call with a confidence phrase and its record per phrase.
T3 conformity: the respondent's own reading against n analysts who all call the opposite, whose
    calls are independent readings, repeats of one analyst's call, or guesses.
T4 relay chains: a call that reaches the respondent through k relays, each of which passes on
    what it was told unchanged with probability f and otherwise a coin flip.
T2 (peer dependence) reuses the copying designs and observer (see disposition_tasks.peers).
"""

import numpy as np

from epistemics.dispositions.fit import BIAS, GAMMA, REPORT_SD, summarize
from epistemics.dispositions.response import logit, report_log_likelihood

# T1. Phrases in order of emphasis, with strength z = -1, 0, 1.
PHRASES = ("hedged", "plain", "emphatic")
RECORD_CALLS = 40
RECORD_HITS = (22, 28, 34, 38)


def record_accuracy(hits, calls=RECORD_CALLS):
    """The accuracy a call with this record carries: its hit rate. (Model 0.11 used the uniform-
    prior mean (K + 1)/(N + 2); in the pilot every configuration used the hit rate, which the texts
    invite and is equally defensible, so model 0.12 takes it as the ideal.)"""
    return np.asarray(hits, dtype=float) / calls


def advice_terms(items):
    """Per case: prior log-odds, the own reading's log-likelihood ratio, the call's ratio given
    its phrase's record, and the phrase's signed strength."""
    prior = logit(np.asarray(items["prior"], dtype=float))
    own = np.asarray(items["own"], dtype=float) * logit(np.asarray(items["own_acc"], dtype=float))
    call = np.asarray(items["call"], dtype=float)
    phrase = np.asarray(items["phrase"], dtype=int)
    hits = np.choose(phrase, [np.asarray(items[f"hits_{h}"]) for h in range(len(PHRASES))])
    rec = call * logit(record_accuracy(hits))
    conf = call * (phrase - 1)
    return prior, own, rec, conf


def advice_answer(items, beta_own=1.0, beta_rec=1.0, beta_conf=0.0):
    prior, own, rec, conf = advice_terms(items)
    return prior + beta_own * own + beta_rec * rec + beta_conf * conf


ADVICE_OWN = np.round(np.arange(0, 1.501, 0.1), 2)
ADVICE_REC = np.round(np.arange(0, 1.501, 0.1), 2)
ADVICE_CONF = np.round(np.arange(-0.6, 1.201, 0.1), 2)


def fit_advice(items, reports):
    """Grid posterior for own weight, record weight, confidence weight, bias and noise."""
    reports = np.asarray(reports, dtype=float)
    prior, own, rec, conf = advice_terms(items)
    means = (
        prior
        + ADVICE_OWN[:, None, None, None, None] * own
        + ADVICE_REC[None, :, None, None, None] * rec
        + ADVICE_CONF[None, None, :, None, None] * conf
        + BIAS[None, None, None, :, None]
    )
    ll = np.stack([report_log_likelihood(means, reports, sd) for sd in REPORT_SD], axis=-1)
    grids = {
        "beta_own": ADVICE_OWN,
        "beta_rec": ADVICE_REC,
        "beta_conf": ADVICE_CONF,
        "bias": BIAS,
        "report_sd": REPORT_SD,
    }
    return summarize(ll, grids)


# T1 open (model 0.12): no record is given, so no ideal exists. The fitted weights are defaults:
# w0, the log-odds weight on a plain call, and w_conf, the change per step of emphasis.
ADVICE_W0 = np.round(np.arange(0, 3.001, 0.1), 2)
ADVICE_WCONF = np.round(np.arange(-1.0, 1.501, 0.1), 2)


def advice_open_answer(items, beta_own=1.0, w0=1.0, w_conf=0.0):
    prior, own, _, conf = advice_terms(items)
    call = np.asarray(items["call"], dtype=float)
    return prior + beta_own * own + w0 * call + w_conf * conf


def fit_advice_open(items, reports):
    """Grid posterior for own weight, default call weight w0, emphasis weight, bias and noise."""
    reports = np.asarray(reports, dtype=float)
    prior, own, _, conf = advice_terms(items)
    call = np.asarray(items["call"], dtype=float)
    means = (
        prior
        + ADVICE_OWN[:, None, None, None, None] * own
        + ADVICE_W0[None, :, None, None, None] * call
        + ADVICE_WCONF[None, None, :, None, None] * conf
        + BIAS[None, None, None, :, None]
    )
    ll = np.stack([report_log_likelihood(means, reports, sd) for sd in REPORT_SD], axis=-1)
    grids = {
        "beta_own": ADVICE_OWN,
        "w0": ADVICE_W0,
        "w_conf": ADVICE_WCONF,
        "bias": BIAS,
        "report_sd": REPORT_SD,
    }
    return summarize(ll, grids)


# T3. Status of the majority's calls: independent readings, repeats of one analyst's call,
# guesses.
STATUSES = ("independent", "dependent", "guess")


def conformity_terms(items):
    """Per case: exact log-odds, the answer that counts every analyst as an independent
    reading, the own reading's term, and the conformity regressor (majority direction times
    log2(1 + n))."""
    prior = logit(np.asarray(items["prior"], dtype=float))
    own = np.asarray(items["own"], dtype=float) * logit(np.asarray(items["own_acc"], dtype=float))
    n = np.asarray(items["n"], dtype=float)
    status = np.asarray(items["status"], dtype=int)
    majority = -np.asarray(items["own"], dtype=float)
    reading = majority * logit(np.asarray(items["peer_acc"], dtype=float))
    peers = np.where(status == 0, n * reading, np.where(status == 1, (n > 0) * reading, 0.0))
    counted = np.where(status == 2, 0.0, n * reading)
    return prior + peers, prior + counted, own, majority * np.log2(1 + n)


def conformity_answers(items):
    """Exact and counted log-odds, with the own reading at full weight."""
    exact, counted, own, _ = conformity_terms(items)
    return exact + own, counted + own


CONFORM_OWN = np.round(np.arange(0, 1.501, 0.1), 2)
CONFORM_ETA = np.round(np.linspace(0, 1, 11), 2)
CONFORM_KAPPA = np.round(np.arange(-0.6, 1.501, 0.1), 2)


def fit_conformity(items, reports):
    """Grid posterior for own weight, dependence neglect eta, conformity kappa, bias, noise."""
    reports = np.asarray(reports, dtype=float)
    exact, counted, own, social = conformity_terms(items)
    peers = (1 - CONFORM_ETA)[:, None] * exact + CONFORM_ETA[:, None] * counted
    means = (
        CONFORM_OWN[:, None, None, None, None] * own
        + peers[None, :, None, None, :]
        + CONFORM_KAPPA[None, None, :, None, None] * social
        + BIAS[None, None, None, :, None]
    )
    ll = np.stack([report_log_likelihood(means, reports, sd) for sd in REPORT_SD], axis=-1)
    grids = {
        "beta_own": CONFORM_OWN,
        "eta": CONFORM_ETA,
        "kappa": CONFORM_KAPPA,
        "bias": BIAS,
        "report_sd": REPORT_SD,
    }
    return summarize(ll, grids)


# T3 open (model 0.12): the majority's evidence is not described. The fitted defaults are v, the
# log-odds weight of one analyst's call, and rho, how the majority's weight grows with its size:
# weight v * n^rho (rho 1 counts every analyst as independent, 0 treats the majority as one).
CONFORM_V = np.round(np.arange(0, 2.001, 0.1), 2)
CONFORM_RHO = np.round(np.arange(0, 1.201, 0.1), 2)


def conformity_open_terms(items):
    prior = logit(np.asarray(items["prior"], dtype=float))
    own = np.asarray(items["own"], dtype=float) * logit(np.asarray(items["own_acc"], dtype=float))
    n = np.asarray(items["n"], dtype=float)
    majority = -np.asarray(items["own"], dtype=float)
    return prior, own, n, majority


def conformity_open_answer(items, beta_own=1.0, v=0.5, rho=1.0):
    prior, own, n, majority = conformity_open_terms(items)
    return prior + beta_own * own + majority * v * np.where(n > 0, n**rho, 0.0)


def fit_conformity_open(items, reports):
    """Grid posterior for own weight, v, rho, bias and noise."""
    reports = np.asarray(reports, dtype=float)
    prior, own, n, majority = conformity_open_terms(items)
    size = np.where(n > 0, n[None, :] ** CONFORM_RHO[:, None], 0.0)
    means = (
        prior
        + CONFORM_OWN[:, None, None, None, None] * own
        + CONFORM_V[None, :, None, None, None] * majority * size[None, None, :, None, :]
        + BIAS[None, None, None, :, None]
    )
    ll = np.stack([report_log_likelihood(means, reports, sd) for sd in REPORT_SD], axis=-1)
    grids = {
        "beta_own": CONFORM_OWN,
        "v": CONFORM_V,
        "rho": CONFORM_RHO,
        "bias": BIAS,
        "report_sd": REPORT_SD,
    }
    return summarize(ll, grids)


# T4. A call's accuracy after k relays with fidelity f: 1/2 + (a - 1/2) f^k.
def relay_accuracy(acc, hops, fidelity):
    return 0.5 + (np.asarray(acc, dtype=float) - 0.5) * np.asarray(fidelity, dtype=float) ** hops


def relay_answer(items, fidelity=None, gamma=1.0):
    """Log-odds when each relay keeps the call with probability `fidelity` (the stated one if
    None), and the call's log-likelihood ratio is scaled by `gamma`."""
    f = np.asarray(items["fidelity"], dtype=float) if fidelity is None else fidelity
    q = relay_accuracy(items["acc"], np.asarray(items["hops"]), f)
    call = np.asarray(items["call"], dtype=float)
    return logit(np.asarray(items["prior"], dtype=float)) + gamma * call * logit(q)


RELAY_OMEGA = np.round(np.arange(0, 2.001, 0.1), 2)
RELAY_FIDELITY = np.round(np.arange(0.3, 1.0001, 0.05), 2)


def fit_relay(items, reports, stated):
    """Stated fidelity: the exponent omega applied to it (f^(omega k); 1 is exact, 0 treats
    relayed calls as first-hand). Unstated: the implied fidelity per relay. Both with the call's
    weight gamma, bias and noise."""
    reports = np.asarray(reports, dtype=float)
    prior = logit(np.asarray(items["prior"], dtype=float))
    call = np.asarray(items["call"], dtype=float)
    hops = np.asarray(items["hops"], dtype=float)
    acc = np.asarray(items["acc"], dtype=float)
    if stated:
        grid, name = RELAY_OMEGA, "omega"
        decay = np.asarray(items["fidelity"], dtype=float)[None, :] ** (grid[:, None] * hops)
    else:
        grid, name = RELAY_FIDELITY, "fidelity"
        decay = grid[:, None] ** hops
    evidence = call * logit(0.5 + (acc - 0.5) * decay)
    means = (
        prior + GAMMA[None, :, None, None] * evidence[:, None, None, :] + BIAS[None, None, :, None]
    )
    ll = np.stack([report_log_likelihood(means, reports, sd) for sd in REPORT_SD], axis=-1)
    grids = {name: grid, "gamma": GAMMA, "bias": BIAS, "report_sd": REPORT_SD}
    return summarize(ll, grids)


# Designs: 24 cases each, seeded; exact answers within 5-95%.
_PRIORS = (0.3, 0.4, 0.5, 0.6, 0.7)
_EDGE = 2.94


def _columns(rows, names):
    return {name: np.array([r[name] for r in rows]) for name in names}


def advice_design():
    """Four record levels for the phrase used x three phrases x (no own reading, own reading
    against the call). The other phrases' records vary, so the phrase used must be matched to
    its own record."""
    rng = np.random.default_rng(20261011)
    rows = []
    for own in (0, 1):
        for hits in RECORD_HITS:
            for phrase in range(len(PHRASES)):
                while True:
                    call = int(rng.choice([-1, 1]))
                    row = {
                        "kind": "advice",
                        "prior": float(rng.choice(_PRIORS)),
                        "own": -call if own else 0,
                        "own_acc": float(rng.choice([0.7, 0.8])),
                        "call": call,
                        "phrase": phrase,
                    }
                    others = rng.choice(RECORD_HITS, len(PHRASES))
                    for h in range(len(PHRASES)):
                        row[f"hits_{h}"] = int(hits if h == phrase else others[h])
                    table = _columns([row], row)
                    if abs(advice_answer(table)[0]) <= _EDGE:
                        rows.append(row)
                        break
    return _columns(rows, rows[0])


def conformity_design():
    """Six cases with only the own reading (anchors for its weight), then majorities of 1, 3 and
    5 analysts under each status, twice each."""
    rng = np.random.default_rng(20261012)
    rows = []

    def draw(n, status):
        while True:
            own = int(rng.choice([-1, 1]))
            row = {
                "kind": "conformity",
                "prior": float(rng.choice(_PRIORS)),
                "own": own,
                "own_acc": float(rng.choice([0.7, 0.8, 0.9])),
                "n": n,
                "status": status,
                "peer_acc": float(rng.choice([0.6, 0.65, 0.7])),
            }
            exact, _ = conformity_answers(_columns([row], row))
            if abs(exact[0]) <= _EDGE:
                return row

    for _ in range(6):
        rows.append(draw(0, 0))
    for n in (1, 3, 5):
        for status in range(len(STATUSES)):
            for _ in range(2):
                rows.append(draw(n, status))
    return _columns(rows, rows[0])


def relay_design():
    """Chains of 0-3 relays x fidelity 60% or 80% x three cases each."""
    rng = np.random.default_rng(20261013)
    rows = []
    for hops in range(4):
        for fidelity in (0.6, 0.8):
            for _ in range(3):
                while True:
                    row = {
                        "kind": "relay",
                        "prior": float(rng.choice(_PRIORS)),
                        "call": int(rng.choice([-1, 1])),
                        "acc": float(rng.choice([0.8, 0.9])),
                        "hops": hops,
                        "fidelity": fidelity,
                    }
                    if abs(relay_answer(_columns([row], row))[0]) <= _EDGE:
                        rows.append(row)
                        break
    return _columns(rows, rows[0])
