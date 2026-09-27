# Research-world generator: design draft

Draft, 27 September 2026, for the [naturalistic disclosure and shared-origin pilot](decision-value-pilot.md#2b-naturalistic-disclosure-and-shared-origin-pilot). It follows the [literature review](literature-review-2026-09-27.md). Nothing here is implemented. Section 8 lists the decisions that need review before implementation. No existing battery, evaluator or evidence changes.

## 1. Purpose

Produce realistic research dossiers about fictional companies whose informational structure is known exactly. Two structures come first:
- **selective disclosure:** a source reveals only favorable facts;
- **shared-origin corroboration:** several documents relay one upstream observation.

Each structure is recoverable only from textual cues such as attribution, identical figures, "as first reported by" and disclosure habits. The generator keeps a private ledger giving the normative posterior for every dossier. The measurement is the difference in a respondent's forecast and decision between two presentations carrying identical information. That difference needs no reference posterior and makes no claim about internal belief.

Target reading-guide claim, **unmeasured**: "Under unprompted conditions this configuration treats relayed corroboration as independent (or ignores what silence implies); require verification when a conclusion rests on such evidence."

## 2. Latent world

A world is one company decision, reusing the existing task's payoff frame.

| Element | Content |
| --- | --- |
| Hypothesis | Demand is strong or weak; public prior from {0.2, 0.5, 0.8}; decision threshold from {0.3, 0.7}; the same payoffs as the current task |
| Evidence atoms | Binary primary observations with disclosed diagnosticity, e.g. a KPI that beats or misses guidance, or a channel check that is positive or negative. P(atom = favorable given strong) and P(atom = favorable given weak) are fixed per atom type |
| Provenance graph | Primary nodes (company data, an analyst's channel check, a customer survey), relay nodes (news reports, newsletters, forum posts) and edges saying which document reproduces which node |
| Senders | Company investor relations, with a disclosure rule; independent analysts, truthful with known accuracy; relays, which reproduce upstream content without adding information unless they state an independent observation |
| Normative ledger | For each document, the atoms it newly reveals; the Bayesian posterior given the true generative process; and the posterior a respondent could reach from the public description of possible processes. That public-information reference is primary, as in the audit |

Atoms are binary so that disclosure pairs can be exactly information-equivalent. Once the rule is known, silence under a disclosure rule reveals the same binary fact as an explicit miss.

## 3. Contrasts

Each family has matched presentations built from the same world and ledger. Respondents see only one member of a pair in a context.

### 3.1 Selective disclosure (after Enke 2020; Jin, Luca & Martin 2021; Farina et al. 2026)

| Presentation | What the dossier shows | Information |
| --- | --- | --- |
| **Full** | The company's quarterly letter lists all four tracked KPIs, each marked beat or missed | Four atoms |
| **Selected** | The letter lists only the beats. A separate earlier document shows that the company tracks and historically reported the same four KPIs. The disclosure habit is recoverable, e.g. "reports KPIs that beat guidance" appears in an earlier letter or an analyst note | Four atoms: omitted KPIs are misses under the recoverable rule |
| **Uninformative silence (control)** | The letter lists only beats, but the dossier establishes that the company never tracked the other KPIs | Fewer atoms; a correct posterior differs from Full |

The primary contrast is Selected minus Full on the log-odds scale. A Bayesian difference is zero. The uninformative-silence control distinguishes "ignores silence" from "distrusts partial letters in general".

### 3.2 Shared-origin corroboration (after Enke & Zimmermann 2019; Schuster et al. 2026; Pilditch et al. 2020)

| Presentation | What the dossier shows | Information |
| --- | --- | --- |
| **Single** | One analyst note reports a positive channel check | One atom |
| **Relayed** | That note plus two or three articles repeating the same figure, each attributing it to the analyst, with overlapping phrasing and later dates | One atom |
| **Independent (scale anchor)** | The note plus two genuinely independent checks with their own methods and figures | Three atoms |

The primary contrast is Relayed minus Single; a Bayesian difference is zero. Independent minus Single gives the scale of a full update. A neglect weight on the log-odds scale is

χ = (update_relayed − update_single) / (update_independent − update_single)

with χ = 0 for a Bayesian and χ = 1 for full double counting. Pilditch et al. show that partially dependent reports can carry extra information. The first version therefore uses pure relays, where dependence adds nothing, and defers partial dependence.

## 4. Arms: noticing versus computing

Each dossier appears in one of three arms, as in Enke & Zimmermann's design:
- **Unprompted:** generic instructions to evaluate the evidence and decide. Provenance and selection are never mentioned. This is the buyer-relevant condition.
- **Hinted:** a single general sentence asking the respondent to consider how each item was produced and whether sources are independent.
- **Explicit:** the same prose plus a stated structure, e.g. "articles B and C repeat note A's figure" or "the company reports only KPIs that beat guidance".

The existing structured source task remains a separate calculation control carrying the audit's calibration comparison. Unprompted minus explicit on the same prose is the noticing gap, and it is the portable fact a reading guide would report.

## 5. Rendering

- **First version: templated rendering.** Several document genres (quarterly letter, analyst note, news brief, newsletter item, forum post), several paraphrase templates per genre, generated entity names and dates, and irrelevant distractor documents. Rendering is deterministic from a rendering seed.
- **Equivalence audit.** A deterministic extractor recovers the atom ledger and provenance edges from every rendered dossier. A dossier is rejected if extraction differs from the ledger, or if paired dossiers differ in anything but the manipulated structure: length, genre mix, distractors and positions are matched within pairs.
- **Later, optional: LLM paraphrase.** An LLM pass adds variety only after the extractor audit and a second independent extractor both confirm the ledger. Its prompts and outputs are stored and hashed.
- **Contamination and recognizability.** Canonical experiments must not be recognizable: no urns, bookbags or published wording. Fictional firms and sectors throughout.

## 6. Elicitation, decision and scoring

- **Per dossier:** a whole-percentage probability of strong demand and invest/decline, delivered through the compact interface (one call per checkpoint).
- **Verification coupling (second stage).** A priced check reveals primary data: the undisclosed KPIs, or an independent channel check. Prices are set so that the check has positive expected value exactly when relayed or selected structure makes the public evidence weaker than it looks. Low-value controls are retained. Score ex ante against the generator, with realized payoff secondary.
- **Contrast estimates.** Estimate within-pair differences on matched worlds across fresh contexts. Pairs are between contexts, because a side-by-side contrast removes neglect in humans. Report per-configuration χ and selection-neglect weights with uncertainty. Compare a two-type (Bayesian or naive) mixture with a continuous weight, since human naivety in these paradigms is close to bimodal.
- **Human reference.** Compare with published human estimates and the downloaded replication data (Enke 2020; Enke & Zimmermann 2019; Jin, Luca & Martin 2021; Farina et al. 2026). Task differences are stated; no fresh human collection is planned for several weeks.

## 7. Validation before any agent collection

1. **Generator checks:** every world's ledger reproduces its stated posterior. Paired dossiers are information-equivalent by construction and by extraction audit.
2. **Synthetic respondents:** Bayesian, fully naive (χ = 1, silence ignored), partial (χ = 0.5), a two-type mixture, and each with reporting noise at the observed 0.2 levels (about 2 and 8 points standard deviation). Recover χ, the selection weight and the mixture share. Report how many independent worlds are needed to separate χ = 0 from χ = 0.5 per configuration.
3. **Decision value:** compute the check's expected value under the generator across worlds, confirming that verification is valuable where the structure is misread and not elsewhere.
4. **Cost:** projected tokens per context using compact-acceptance measurements.

## 8. Decisions needed before implementation

1. **Domain.** Stay with fictional company due diligence (continuity with the payoff frame and existing controls), or render a second domain from the start to limit presentation-specific findings?
2. **Rendering.** Templated first, with LLM paraphrase later, as proposed; or LLM-rendered prose from the start with extraction audits?
3. **Pairing.** Contrasts between contexts on matched worlds, as proposed; or also within a context across companies, which is cheaper but risks contrast effects?
4. **Explicit arms.** Keep both the rendered-explicit arm and the existing numeric task, or drop one?
5. **Active inspection.** Allow the respondent to request provenance details (who first reported a figure, the company's past disclosure practice) as a priced action? This adds the check-generation dimension the literature identifies, but complicates scoring.
6. **Pilot scale.** Suggested: two configurations × two families × three arms, with enough independent worlds to separate χ = 0 from χ = 0.5, set from the synthetic precision estimate and the compact acceptance's measured cost.
