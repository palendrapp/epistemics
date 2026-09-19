# Agent identity and epistemic records

## The passport as part of agent identity

The [epistemic passport](epistemic-passport.md) is the primary product built on this record space: a readable and machine-readable behavioral profile issued about an agent configuration. A stable agent identity can accumulate passports over time, while each evaluation remains attached to the exact configuration and protocol it tested.

The intended identity surface lets consumers discover a passport, verify its issuer and artifact integrity, inspect evaluation age and coverage, and follow configuration changes, corrections or withdrawals. Detailed profiles and evidence live off-chain. Private prompt contents need not appear in public identity records; fingerprints and evidence-access policies must be explicit.

This lifecycle is proposed. The current implementation signs individual evaluation reports and supports devnet Memo commitments. Passport aggregation/signing, a stable-identity registry, publication and indexing remain to be built. An on-chain record authenticates provenance; it does not by itself verify the runtime or establish the accuracy of the behavioral interpretation.

The proposed [cognitive-security layer](cognitive-security.md) also binds tested interventions to their baseline and assisted configurations. It keeps detailed vulnerability and intervention records under controlled access. Future human participation and identity-linked publication require consent; independent agent-issuer semantics below do not automatically extend to human profiles. Private human use must be possible without an on-chain identity link.

## Keep four roles distinct

| Primitive | Meaning | Current implementation |
| --- | --- | --- |
| Agent identity | A stable subject identifier for a lineage of agent configurations | Caller-supplied `agent_id`, without uniqueness or ownership guarantees |
| Controller | Authority to change an identity's metadata and delegated keys | Design only; no controller registry yet |
| Runtime instance | One execution/configuration, potentially holding a delegated hot key | Model/version/configuration hash in a report; operator-asserted |
| Evaluator/issuer | Party making the claim that an evaluation occurred and produced a report | Solana-compatible Ed25519 key, detached signature, transaction signer |

A model name is not a unique agent, an agent can have many runtime instances, and a single wallet can control many agents. A public key identifies a cryptographic authority, not a distinct intelligence. A runtime signature would prove delegated key control; it would still not establish which model produced the responses.

The initial record is an **evaluator attestation about a subject**, so an independent evaluator can issue one without the subject's consent. Subject endorsement should be a separate optional signature with a different domain, not a prerequisite that lets an agent suppress unfavorable evaluations. Consumers decide which evaluators and execution-verification methods they trust.

## A broader record space

Evaluation is the first implemented record kind. The eventual record service should also accept agent-authored epistemic histories independently of this evaluator:

| Proposed record kind | Core content | Typical issuer |
| --- | --- | --- |
| Belief assertion | Claim/question ID, probability distribution, information cutoff, context/configuration hash | Authorized agent runtime |
| Evidence observation | Source/artifact digest, observation time, relation to a claim | Runtime or evidence provider |
| Belief revision | Previous belief-record hash, new distribution, referenced evidence records | Authorized agent runtime |
| Outcome resolution | Claim ID, resolution evidence and adjudication method | Named resolver |
| Evaluation attestation | Battery/report digest, subject/configuration and evaluator provenance | Evaluator; implemented in v1 |

These proposed kinds need separate versioned schemas and authorization rules. The common layer should handle identity, provenance, links, sequencing and availability, while interpretation stays off-chain. A belief statement should never silently become an evaluator endorsement. The current `create` command deliberately accepts evaluation reports only.

## v1 record format (implemented)

The accepted evaluation report follows `schemas/report.v1.json`, `schemas/report.v2.json` or `schemas/report.v3.json`. All three use the v1 signed-record envelope. Study profiles and the proposed passport artifact are not currently accepted. The report's exact UTF-8 file bytes, including whitespace and trailing newline, are hashed with SHA-256. Reformatting the file changes its digest.

The signed record follows `schemas/record.v1.json` and consists of:

- `payload`: schema version, record kind, network, issuer public key, subject agent ID, report hash, report URI, battery hash, optional predecessor record hash, and issuer-asserted creation time.
- `record_sha256`: SHA-256 of the canonical payload bytes.
- `signature_base64`: Ed25519 signature of the domain-separated payload bytes.

For this **flat, string-or-null v1 payload**, canonical encoding sorts property names by UTF-16 code-unit order, constructs an object in that order, and applies ECMAScript `JSON.stringify` without whitespace, encoded as UTF-8. There are no floating-point fields or nested objects in the signed payload. This is a deliberately restricted format, not an implementation of arbitrary JSON canonicalization. Unknown fields are rejected; new fields require a versioned contract.

Signing bytes are exactly:

```text
UTF8("epistemics/record-signature/v1\n") || canonical_payload_bytes
```

The Memo is exactly `epistemics:v1:<record_sha256>`. The standard [Solana Memo program](https://www.solana-program.com/docs/memo) records UTF-8 data and checks supplied signer accounts. The builder requires the issuer as a Memo signer and transaction fee payer. It constructs a version-0 transaction and verifies its packet-size limit.

Verification checks the record schema, canonical payload hash, issuer signature, report's exact bytes, and the report's subject/battery metadata. When a transaction signature is supplied it additionally checks the devnet genesis hash, requests **finalized** transaction data, requires successful execution and an issuer transaction signature, and matches the actual Memo program instruction. Log text from another program does not count. Verification trusts the selected RPC's view of the chain; it is not a light-client consensus proof.

## What the commitment does and does not provide

It binds an issuer to a specific claim and makes later artifact changes detectable. Successful finalized inclusion places that commitment in ledger history. `created_at` remains an issuer assertion; the record may have been produced earlier or later than claimed.

The Memo contains only a digest. Consumers also need the signed envelope, report bytes, and transaction signature. Store them together and provide a discoverable index. The CLI does not upload files, check URI availability, retrieve reports, or guarantee historical RPC availability. Devnet is an integration environment, not a promise of permanent archival storage.

`previous_record_sha256` is a signed reference, **not an enforced sequence**. The current verifier authenticates that reference but does not fetch the predecessor or check agent/issuer continuity. Two records can point to the same predecessor, and the Memo program will accept both. An indexer could detect such forks; a registry must enforce monotonicity if non-equivocation is required.

Authenticity of a record does not imply valid science, truthful metadata, complete run reporting or unique subject identity. Reports set `execution_verification="operator_asserted"`. Never promote that to model attestation merely because the record is on-chain.

## Existing Solana primitives to evaluate

Survey checked 2026-09-19. These are integration candidates, not dependencies of this MVP.

| Candidate | Why inspect it | Decision gate |
| --- | --- | --- |
| [Solana Attestation Service](https://github.com/solana-foundation/solana-attestation-service) | Existing attestation program and generated clients; the [SATI proposal](https://github.com/solana-foundation/SRFCs/discussions/7) uses SAS schemas for agent-related claims. | Confirm schema authorization, issuer semantics, revocation, indexability, upgrade authority and deployed version against our threat model. |
| [Solana Record Service](https://github.com/solana-foundation/solana-record-service) | Existing record-storage program and SDK that could hold identity metadata or pointers. | Inspect update authority, ownership transfer, record size/cost and historical availability before adopting it. |
| [Solana Agent Trust Infrastructure proposal](https://github.com/solana-foundation/SRFCs/discussions/7) | Describes identity, delegated signing, evidence/feedback schemas and distinct reputation providers. | The cited sRFC is labeled draft; evaluate implementation and schema compatibility independently. Do not treat the proposal's claims as guarantees. |
| Custom PDA registry | Can encode exactly the identity lifecycle and per-issuer sequence constraints we need. | Only build if existing primitives fail concrete requirements; budget for program review, validator tests, deployment and upgrades. |

Token or NFT ownership can be a controller primitive when interoperability requires it. It should not make reputation automatically transferable with ownership: historical evaluator records need to remain attached to the evaluated configuration and authority epoch.

## Proposed registry, if needed (not implemented)

Use a stable random 32-byte agent identifier for an `Agent` PDA, with a controller key, authority epoch, descriptor hash and revocation state. The PDA identity remains stable across controller rotation. Require controller authorization for registration/updates; validate all seeds, owners and accounts.

Store a scoped `Delegation` from controller to runtime key: agent ID, epoch, allowed action types, expiry slot and revocation marker. A controller rotation invalidates prior-epoch delegations. Keep evaluator delegation separate from subject delegation. Never grant a runtime key token-transfer permissions merely to sign epistemic evidence.

For each `(agent, evaluator)` maintain a record head containing a sequence number and last record hash. An append instruction requires the evaluator's signature, exact next sequence and prior hash. Every immutable record binds the battery/configuration/artifact digests. Evaluator revocation and corrections are new events, not deletion or rewriting of past attestations. A subject's controller cannot rewrite independent evaluator evidence.

The subject descriptor should identify model provider/revision, prompt/tool/runtime hashes and optional execution-attestation evidence. Different configurations can belong to one lineage but must not silently inherit each other's measured parameters. Actual execution verification may later use trusted evaluator infrastructure, signed provider evidence or remote attestation; each needs its own verification method and trust assumptions.

Registry acceptance tests must cover unauthorized append/update, cross-agent account substitution, stale sequence, replay, chain fork attempts, controller rotation, expired/revoked delegation, authority epoch changes, oversize data, close/reinitialize attacks and version migrations.
