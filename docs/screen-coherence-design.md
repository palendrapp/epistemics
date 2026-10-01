# Coherence sets for the open-inference screen (design note)

Design, 1 October 2026; built the same day (model 0.19.0, design 0.20.0, tasks 0.29.0; see [Built](#built)). Nothing is collected yet.

## Why

**Coherence is the lead construct** chosen in the 30 September design critique: agreement between two things an agent does that should be governed by one belief. It needs no right answer, it compares behaviour with behaviour, and it is the passport's question: does this agent act on the probabilities it states?

**So far it has been at ceiling wherever the link was stated.**
- In battery v3, bets were priced at exactly 100 × the stated probability.
- In v3.1, every decision switched at exactly 50% of the configuration's own stated belief.

When a task spells out how two answers relate, frontier agents keep them consistent.

**It reappears where nothing is stated.** In the screen's F4 items (stages A and B), a configuration's direct answer to "none of these" can be set against the probability that its answers about the listed causes leave over: 1 − *k* × P(a listed cause).
- **GPT-6 configurations** are coherent: gaps of −0.11 to +0.06.
- **GPT-5.6 is not.** Asked directly, it allows 0.10–0.17 for causes not listed. But its answers about the listed causes add up to nearly all the probability (Luna: implied 0.00; Terra: 0.04–0.14). That is the unpacking effect of support theory (Tversky & Koehler 1994).

It is the same family split as battery v2's one transferring result: GPT-5.6 stated base rates its forecasts did not use.

**The hypothesis.** Incoherence that shows only when the model is left open is a general trait: the same configurations violate the laws of probability across families, and reliably.

## Coherence sets

A **coherence set** is a few questions about one unstated model whose answers are tied together by a law of probability. The law holds **whatever the model**, so a departure is incoherence, not a different prior: the screen's prior differences cannot produce it.

| Law | Set | Coherent answers |
| --- | --- | --- |
| Partition | Every part of an exhaustive partition (each listed cause and "none of these"; the bins of a range) | Sum to 1 |
| Complement | An event and its negation ("more than 30" and "30 or less") | Sum to 1 |
| Packing | A packed description and its parts ("an electrical fault" against "a power fault" and "a control fault") | Packed = sum of parts |
| Conjunction and disjunction | A, B, A and B, A or B | P(A) + P(B) − P(A and B) − P(A or B) = 0 |
| Nesting | A narrow window inside a wide one | Narrow ≤ wide |

**Every member is its own case.** The members of a set are separate cases with the same text and different questions, at least four cases apart in random order. Nothing in a case says it belongs to a set. An agent that keeps a set coherent across separate encounters is coherent; that is what we want to know.

## The model: a Bayesian sampler

Incoherence has a Bayesian account, in the Oaksford–Chater tradition.

**The Bayesian sampler** (Zhu, Sanborn & Chater 2020) estimates a probability from *N* mental samples, regularised by a symmetric prior with weight *β*. The expected estimate is (*N*·*p* + *β*)/(*N* + 2*β*): pulled towards 0.5 by *d* = *β*/(*N* + 2*β*). Probability theory plus noise (Costello & Watts 2014) is the closely related account without the prior. Zhu & Griffiths (2024) applied these identities to language models' probability judgements.

**Its predictions are specific:**
- **Complements** sum to 1 on average, whatever *d*.
- **A *k*-part partition** sums to (*N* + *k*·*β*)/(*N* + 2*β*) on average: subadditivity that grows with the number of parts, with slope *d* per extra part. Partitions of 2, 3 and 5 parts identify *d*.
- **The identity** P(A) + P(B) − P(A and B) − P(A or B) is 0 on average. This separates the sampler from support-theory accounts, under which unpacked descriptions gain support systematically.
- **Variability:** the spread of repeated estimates falls with *N*.

**Its parameters are a configuration's profile:**
- *d*, the shrinkage towards 0.5 (conservatism);
- *N*, sampling precision.

Both are Bayesian in form, and are candidates for a trait that is general across families.

**It may unify two earlier findings.** The fallback round found that configurations hedge towards a default on open items and not at all on fixed-answer items. The sampler predicts exactly that, *if* open items are answered by sampling (simulation under uncertainty) and computable items by calculation. So the sets come in two kinds:
- **open sets,** whose members depend on the family observer's parameters;
- **computable sets,** whose members are fixed under it (like form c's fallback items).

Prediction: shrinkage and subadditivity on open sets, none on computable sets.

## Bias and variance

You asked what role bias plays, if coherence is effectively variance. It is not quite: incoherence has a bias part and a variance part, and coherent answers can still be biased.

**An answer has three components beyond the norm:**

| Component | What it is | Coherent? | Where it is measured |
| --- | --- | --- | --- |
| Coherent bias | A different prior or model, applied consistently: Luna's closed-world prior, a high rule weight, a belief in exact processes | Yes: every law holds given the agent's own model | The screen's profiles (*λ*, *π*, *ρ*, *w*, *δ*) |
| Incoherent bias | A systematic distortion that breaks the laws in a consistent direction: estimates shrunk towards 0.5, so partitions sum above 1 by more the more parts they have | No | *d*: the mean signed excess and its growth with *k* |
| Variance | Random scatter: a set sums to 1 on average but not on each occasion | No, case by case | *N* (sampling precision) and report noise: the spread of excesses around their mean |

Coherence violations come only from the second and third rows. The sets separate them:
- **bias:** the mean excess, and its slope over the number of parts;
- **variance:** the spread around that mean.

The first row needs a ground truth or a norm to be called a bias at all. That is why the screen measured it as a prior, not as an error.

**The Bayesian sampler links the two.** With few samples (small *N*), a raw frequency estimate is noisy. The prior's pull towards 0.5 (*d* = *β*/(*N* + 2*β*)) cuts that variance at the price of a systematic bias. This is shrinkage, which lowers expected squared error when samples are few. On this account incoherence is the signature of an agent regularising noisy estimates: rational in its own terms, but incoherent across questions (Zhu, Sanborn & Chater 2020). A configuration's (*d*, *N*) says where it sits on that bias–variance trade-off.

**The consumer action differs:**
- **Incoherent bias is correctable.** A known shrinkage can be inverted: *p* = ((*N* + 2*β*)·*p̂* − *β*)/*N*. A reading guide can say "these probabilities are pulled towards 50%; stretch them like this".
- **Variance is not correctable, only averaged:** ask several times, or several agents.
- **Coherent bias is not visible to coherence tests at all;** it needs the screen's profiles.

**One measurement caution.** Our report noise sits on the log-odds scale, and noise there is not mean-zero on the probability scale: small probabilities come out inflated on average. Pure variance in reporting would then look like incoherent bias, mild subadditivity, in partitions with many small parts. Validation step 2 calibrates exactly this, and the sampler is fitted with the report noise as a separate term.

## Sets per family

**Families.** F2, F4 and F5, the families with reliable differences in stage B. F1 (not reliable) and F3 (an anchor wording problem) are left out.

| Family | Open sets | Computable sets |
| --- | --- | --- |
| F4 unlisted causes | Partitions: each of *k* listed causes and "none of these" (*k* = 2, 3, 5, so 3, 4 and 6 members). Packing: "an electrical fault" against its parts | Conditional partitions: "if the cause was one of those listed, what is the probability that it was X?", over all *k* listed causes (fixed at 1/*k* each) |
| F2 reported numbers | Bins of a person's round number: less than, around, more than (3 parts), and 5 bins. Nesting: ±1 inside ±3. Complements: "more than 30" against "30 or less" | Wide bins whose answers are fixed (0, 1) |
| F5 extrapolation | Bins of the reading at hour 8 (3 and 5 parts). Conjunction and disjunction: A = "above *t* at 8", B = "above *t*′ at 10" | Thresholds far below or far above every projection |

**Sessions.** One module per family and form: 20 set members and 4 coherence anchors. The anchors are cases that state the probabilities, so the set sums trivially; they check comprehension, as in the screen. A form has about five sets: two or three open partitions of different sizes, one other open set (packing, nesting or the identity) and one computable set.

There are two parallel forms, `d` and `e`, for the retest.

## Analysis (to be preregistered before collection)

**Per set:**
- the signed excess, sum of members − 1 (probability scale);
- for identity sets, the identity's value;
- for nesting sets, whether the narrow window exceeds the wide one.

**Per configuration and family:** the Bayesian sampler fitted to all sets jointly (*d*, *N*, report noise; grid posterior), separately for open and computable sets.

**Hypotheses:**
1. **Systematic incoherence.** On open sets, some configurations' partition excess is above 0 and grows with *k*: *d*'s 90% interval above 0.
2. **Open against computable.** *d* is larger on open sets than on computable sets, for most configurations.
3. **Reliable differences.** Configurations' *d* agree across forms `d` and `e` (the stage B test: consistency ICC ≥ 0.5, permutation *p* < 0.05, Holm across the three families).
4. **Directional, from F4 and battery v2.** Luna and Terra have larger *d* than every GPT-6 configuration, in each family.
5. **Exploratory (general trait).** Configurations' *d* correlate across families. With eight configurations this is descriptive only.

## Validation before collection

1. **Recovery.** Simulated Bayesian samplers (*d* and *N* across plausible ranges, plus our report noise), through the real sets. Criteria as for the screen's profiles: *r* ≥ 0.8, coverage ≥ 0.8, confusion ≤ 0.3.
2. **The noise artefact.** Noise added on the log-odds scale is not mean-zero on the probability scale: small probabilities are inflated on average. Report noise alone can therefore make partitions of small parts look subadditive. Coherent observers with our report noise must give a fitted *d* near 0; this calibrates the hypothesis 1 test.
3. **Task validation** on two seeds, with audits:
   - every set's members share the case text;
   - members are at least four cases apart;
   - the computable sets are fixed under the family observers.

## Cost (provisional)

- **Stage A** (form `d`): 3 families × 8 configurations, 24 sessions, about 11 million tokens.
- **Stage B** (form `e`): the same, about 11 million, for the families where stage A shows differences.

## Risks

- **Ceiling again.** Agents may recognise the sets and make them sum by arithmetic. Separating the members limits this. If GPT-6 stays coherent even so, that is a finding: these configurations keep open beliefs coherent. F4 already shows GPT-5.6 does not.
- **Repeated text.** Seeing the same case several times may prompt the agent to recall earlier answers. Under the battery instructions each case is separate, but agents may still notice. Whether it recalls or recomputes, consistency is coherence, so this does not bias the measure, only its interpretation.
- **The sampler may not fit.** Then the model-free excesses still measure coherence, and the misfit says which law is broken (partitions, packing or the identity), which tells sampling and support-theory accounts apart.

## Decisions for you

1. **Families:** F2, F4 and F5 (recommended), or F4 alone first (it already shows the effect; 8 sessions, about 4 million tokens).
2. **Model:** the Bayesian sampler as the profile model (recommended), with support theory as the rival.
3. **Two stages** (recommended), or forms `d` and `e` together.
4. **Budget:** about 11 million for stage A.

## Built

Built on 1 October 2026 as model 0.19.0, design 0.20.0, tasks 0.29.0. The decisions were taken as recommended:
- F2, F4 and F5;
- the Bayesian sampler, with support theory's signature read from the identity sets;
- two stages.

**Code:**
- **Designs, fit and simulated respondents:** `dispositions/cohere.py`.
- **Texts:** `disposition_tasks/cohere_texts.py`.
- **Ledger:** `ledger/cohere_sets.py` and the commands `cohere-validation`, `cohere-a` and `cohere-b`.
- **Modules:** `cohere-{num,lists,trend}-{d,e}`, variant `cohere`.
- **Order policy `sets`:** members of each set at least 4 cases apart, placed largest set first. The runner requires it for these modules and refuses it elsewhere.
- **Stage A preset:** `cohere-a`, 24 runs.

**Sets per form** (20 members and 4 anchors; members of a set share their case text):

| Family | Open sets | Computable sets |
| --- | --- | --- |
| F2 | 3-bin and 5-bin partitions of a person's round number; an A/B identity set; a nesting pair (sharp number) | A complement ("more than 40", "at most 40", 0.5 each); a 4-bin partition of an instrument reading |
| F4 | Partitions of 2, 3 and 5 listed causes plus "none of these"; a disjunction (A, B, A or B) | A conditional 4-cause partition (1/4 each) |
| F5 | 3-bin and 5-bin partitions of a geometric series at hour 8; an identity set; a nesting pair | Two 3-bin partitions with fixed answers (0, 1, 0) |

**Audits:**
- every set shares one case and has distinct questions;
- computable members are fixed under the family observers (openness 0);
- a `sets` order keeps members apart;
- no case shows a percentage, and no open case uses a rate or likelihood word.

Median openness of open members: F2 1.5–1.6, F4 0.7–0.8, F5 4.9–5.4.

**The fit.** Each set's events are sums of disjoint atoms. The atoms have a Dirichlet(*α*) prior, and each answer is logit((1 − 2*d*)·*p* + *d*) plus noise *τ* on the log-odds scale. The grid posterior covers *d* (0–0.3), *τ* and *α*, with *α* shared by a session's sets and integrated out.

**Deviation from the note: the evenness *α*.** With *α* fixed at 1 (uniform over the simplex), coherent respondents whose beliefs are spread evenly over a set's parts, like listed causes, were read as shrunk. 30–45% of them were called incoherent in F4, rising with report noise. Data generated from the fit's own model gave only 2–4%, so this was a mismatch, not integration error. With *α* integrated out, evenness has its own parameter and only the sums inform *d*.

**Validation** (`output/cohere-validation-20261001.json`). 150 simulated respondents per family; their latent beliefs come from the family observers, not the fit's prior; *d* is drawn from 0–0.25 and *τ* from 0.05–0.5. One session's open sets:

| Family | *d* recovery *r* | 90% coverage | Confusion with *τ* | Coherent respondents called incoherent |
| --- | --- | --- | --- | --- |
| F2 | 0.96 | 0.95 | 0.18 | 0% |
| F4 | 0.92 | 0.91 | 0.14 | 7% |
| F5 | 0.94 | 0.91 | −0.09 | 5% |

All pass (*r* ≥ 0.8, coverage ≥ 0.8, confusion ≤ 0.3, false incoherence ≤ 10%). *τ* recovers less well (0.65–0.76), as expected for a single answer per question. In simulation, a partition's answers sum to 1 + (*k* − 2)·*d* (tested).

**Task validation 0.29.** It passed on both seeds: 3,504 cases and 151 contexts. The six coherence-set contexts per seed recover a respondent's *d* (0.08, report noise 0.05) within 0.012, against a tolerance of 0.05.
- Fingerprint `e3e31a91870434a57c38996d584d4cfeaecb47026a86de53faf79eed76b102e0`.
- Seed 20260927: `318c799259c570631d1c875f9597be8a93556b43b95d17c48cb21abb632b9c69`.
- Seed 20261027: `ca31e578339d7ff5dad8ef3991a8192429efe21f374ebefa600340ed74c3c042`.

### Stage A

- **Sessions:** preset `cohere-a`, 24 sessions (eight configurations × F2, F4 and F5, form `d`, `sets` order).
- **Limits:** cap 15 million tokens (about 11 million expected), 1,800 seconds per run.
- **Analysis:** `uv run python -m epistemics.ledger cohere-a <root> --output <file>`. It reports per configuration and family: *d* for open and computable sets, *τ*, each law's residual, and hypotheses 1, 2 and 4.

## Stage A results (1 October)

**Collection.** The first collection (`output/cohere-stage-a-20261001`) stopped after 12 of 24 sessions. The machine slept, two runs passed their wall-clock deadline after 82 seconds of activity, and admission stopped. The other 12 sessions were collected unchanged (same fingerprint and validations) in `output/cohere-stage-a-20261001-topup`; the two partial sessions are discarded.
- 24 sessions; 11.4 million tokens counted, plus the two partial runs, whose usage was not recorded.
- No tool errors. Every session passed its anchors.
- Summary: `output/cohere-stage-a-summary-20261001.json`.

**Preregistered hypotheses (form `d`):**

| Hypothesis | F2 | F4 | F5 |
| --- | --- | --- | --- |
| H1: open *d*'s 90% interval above 0 | none | Terra | Sol, Sol-low |
| H2: open *d* above computable *d* | 8 of 8 (holds) | 2 of 8 (fails) | 8 of 8 (holds) |
| H4: Luna and Terra above every GPT-6 configuration | fails (neither) | fails (Terra only) | fails (neither) |

H2 compares posterior means, so its verdict mostly reflects how informative the computable sets are:
- In F2 and F5, every configuration answers the computable sets exactly. Computable *d* is pinned at 0, and any open *d* above 0, even Luna's 0.002, passes.
- F4 has one computable set. It leaves *d* weakly identified (posterior mean 0.02–0.05, from the prior), so coherent configurations fail.
- Where *d* is clearly above 0 (Terra in F4; Sol and Sol-low in F5), open *d* is above computable *d*.

**Open-set *d* (posterior mean):**

| Configuration | F2 | F4 | F5 |
| --- | --- | --- | --- |
| Astra | 0.003 | 0.010 | 0.026 |
| Astra-low | 0.032 | 0.003 | 0.042 |
| Astra-high | 0.017 | 0.008 | 0.031 |
| Sol | 0.022 | 0.011 | **0.103** |
| Sol-low | 0.053 | 0.041 | **0.078** |
| Sol-high | 0.037 | 0.011 | 0.019 |
| Luna | 0.002 | 0.018 | 0.000 |
| Terra | 0.018 | **0.078** | 0.008 |

Bold: 90% interval above 0.

**What the answers show.** The model-free residuals tell more than *d*.
1. **Most answers are coherent.**
   - In 13 of 24 sessions every open partition sums to 1 within 0.02. One more, Astra's F4 session, has a single 0.05 excess.
   - Disjunctions hold exactly in every F4 session.
   - Nesting is never violated: the narrow window is never above the wide one.
   - Computable sets hold within 0.01, except Luna and Terra in F2 (0.03–0.05).
2. **F4: listed causes at 1/*n*, with "none of these" answered on top.**
   - Terra and Sol-low give each listed cause exactly 1/*n* of the listed causes (0.5, 0.33, 0.2), so the listed causes alone sum to 1.
   - They then answer "none of these" separately: Terra 0.30, 0.25, 0.20; Sol-low 0.20, 0.15, 0.10. Luna does the same with 0.05.
   - The excess therefore equals the "none" answer. It falls as more causes are listed (Terra 0.30, 0.24, 0.20 for 3, 4 and 6 parts), the reverse of the sampler's (*k* − 2)·*d*.
   - The sampler also predicts a disjunction residual of *d*. Terra's is 0 at a fitted *d* of 0.08.
   - Other GPT-6 configurations keep the sum in one of two ways. Astra shrinks the listed causes, leaving 0.25–0.40 for "none". Sol and Sol-high, with five causes listed, give 0.2 each and "none" 0.
   - This is partition dependence: answers biased towards 1/*n* over the options the question names (Fox & Rottenstreich 2003; Fox & Clemen 2005). Here *n* is the listed causes, and the residual category is judged on its own.
3. **F5 (and F2 for some): fine partitions over-sum where coarse ones do not.**
   - 3-bin partitions sum to 1 in every F5 session, but 5-bin partitions over-sum: Sol 1.37, Sol-low 1.24, Luna 1.15. In F2: Sol-low 1.20, Sol-high 1.11.
   - The sampler predicts the 3-bin excess at a third of the 5-bin excess, here 0.08–0.12; it is 0.
   - The identity sets stay near 0 for Sol and Sol-low in F5 (0.01, −0.04), so this is not general subadditivity of disjunctions. Sol-low's F2 identity is the exception (0.16).
4. **Other departures.**
   - Terra's F2 partitions under-sum (0.91, 0.93). The sampler cannot produce this, since *d* ≥ 0.
   - Luna's F2 departures go both ways: 3-bin +0.15, 5-bin +0.06, identity −0.10, computable complement +0.05, with report noise *τ* 0.39. This is noise more than a systematic bias.

**Exploratory (H5, descriptive).**
- Open *d* correlates weakly across families: *r* 0.13 for F2–F4, 0.49 for F2–F5, −0.17 for F4–F5.
- Sol-low is the only configuration above 0.04 in all three families (mean 0.057, the highest).

**Reading.** These results are conditional on these sets and wordings.
- Under the battery instructions, most configurations keep their answers to open questions coherent. The laws hold within 0.02 for Astra-low and Astra-high in every family; for Astra except one 0.05; and for Sol in F2 and F4.
- Incoherence appears in specific configuration × family cells: Terra and Sol-low in F4; Sol, Sol-low and Luna in F5's fine partitions.
- H4 fails: in these sets, GPT-5.6 is not generally less coherent than GPT-6. Low reasoning effort (Sol-low) shows the clearest incoherence.
- The incoherence is not mainly Bayesian-sampler shrinkage. Its signatures are absent: excess growing linearly with *k*, and a disjunction residual of *d*.
- The fitted *d* summarises excess, not a process parameter. The model-free residuals, read per law, are the measurements that separate configurations here. Whether they are reliable is stage B's question.

**Model consequence: the sampler is a special case of partition dependence.**
- The sampler's mean, (1 − 2*d*)·*p* + *d*, equals (1 − *w*)·*p* + *w*·½ with *w* = 2*d*. That is shrinkage towards the ignorance prior of the binary partition {A, not A}.
- Partition dependence generalises it: each answer shrinks towards 1/*n* for the partition the question suggests.
- Two candidate parameters follow: a weight *w* and which partition is salient. In F4, *n* is the listed causes; for a single event, *n* = 2, which is the sampler.
- With *w* = 1 over the listed causes and "none" answered from the case, a partition sums to 1 + *p*(none). That is Terra's pattern exactly.
- F5's fine-partition excess is not explained by this yet.

