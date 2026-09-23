# Resolve, verify, decide — local consumer 0.1

The TypeScript consumer now resolves a pinned devnet agent identity, retrieves a controller-authorized passport reference, verifies the issuer and current signed status, and applies a versioned buyer policy. Its result is `eligible`, `review_required` or `ineligible`, with reasons and exact request/policy/artifact digests. It never sends the proposed service request or authorizes payment.

This is a local integration increment. The complete decision path is covered by synthetic fixtures with mocked registry RPC and actual private loopback HTTP. The [provider enrollment workflow](provider-enrollment.md) additionally binds identity before collection, checks it again before issuance and supplies a fresh synthetic collection preview. A separate live devnet read verified the registry deployment and decoded a public agent identity. There has been no registry write, funded transaction, facilitator call, mainnet validation, public hosting deployment or purchase. Provisional profile thresholds remain buyer choices; this implementation adds no evidence of predictive or intervention benefit.

## Contracts and trust boundaries

| Contract | Binds / purpose |
| --- | --- |
| Existing `passport.v2` and `passport-attestation.v1` | Unchanged measurement artifact and issuer signature; exact file bytes remain valid |
| `provider-binding.v1` | Current controller or authorized operational wallet signs chain/program/asset, controller, subject, configuration, passport digest and URIs, endpoint, payee, payment network/asset and validity window |
| `passport-status.v1` | Issuer signs attestation digest, evaluated controller, sequence, predecessor digest, active/withdrawn/corrected state, replacement digest, reason and validity window |
| `consumer-policy.v1` | Buyer chooses task, issuer/status service, exact protocol/interpretation, freshness, assurance, measurement/uncertainty requirements and maximum payment |
| `consumer-request.v1` | Exact subject/configuration, task, endpoint, POST-body digest, payment network/asset/payee/maximum amount and request nonce |
| `consumer-decision.v1` | Recommendation and reasons, mapped observations, exact input digests, registry snapshot/status commitments and expiry; always `payment_authorized=false` |

Schemas live in `schemas/`; regenerate these additive contracts with `.venv/bin/python scripts/consumer_schemas.py`. This does not change the Python report contract, experimental behavior, evaluator version, frozen benchmark implementation or passport interpretation.

New signed payloads contain only strings. Canonicalization sorts property names in UTF-16 order and uses ECMAScript `JSON.stringify` followed by UTF-8 encoding, as in the existing restricted attestation convention. Ed25519 signs a distinct domain followed by those bytes: `epistemics/provider-binding-signature/v1\n` or `epistemics/passport-status-signature/v1\n`. Unknown fields and invalid signatures are rejected. These envelopes cannot substitute for each other or for passport attestations.

Provider metadata is a discovery hint. A registry `agent_uri` may advertise `extensions.epistemics.provider_binding_uri`; alternatively the operator can provide a binding URI. Neither route grants trust. The binding must match current on-chain authority and the exact requested provider. The issuer key and status-service URI come from the buyer policy, not from untrusted provider metadata.

Issuer, current controller, operational wallet, evaluated subject, reported configuration and execution assurance remain separate. A controller can explicitly designate a different payee. The buyer must request that payee and the signed binding must agree. A configuration digest is an assertion about the evaluated/current configuration, not independent proof of which model will serve a later request.

## Pinned devnet adapter

The read-only adapter uses the existing Solana Kit dependency and a small bounded decoder. It does not install or execute the upstream SDK. Reviewed source pins:

- [8004 TypeScript SDK, 67a896a](https://github.com/QuantuLabs/8004-solana-ts/tree/67a896a6a871ca333c59b99fd73882d07d659959): program IDs and account/PDA conventions.
- [Registry program and IDL, 6b344c9](https://github.com/QuantuLabs/8004-solana/tree/6b344c9c71871daa35f649a6260e180be33c6810): AgentAccount layout, authoritative Core ownership and wallet reset behavior. Exact IDL SHA-256: `b5109accd8efb8bb8a35121fc9108a1aaefcd096401a9a65e6003720c99bdeb1`.
- [Metaplex Core, e72d63e](https://github.com/metaplex-foundation/mpl-core/tree/e72d63e4118a0a95ac9b40221e81b19d49e1e102): uncompressed AssetV1, collection association and current owner layout.

The adapter checks devnet genesis, both executable program accounts and upgradeable-loader ownership, ProgramData pointers, upgrade authorities and exact ProgramData hashes. It reads those four accounts plus the derived agent PDA and Core asset in **one finalized RPC snapshot**. It checks account owners, discriminators, bounded strings, option tags, PDA bump, asset association and registered collection. A changed deployment returns review until a reviewed code update repins it.

| Program | Address | Observed ProgramData SHA-256 |
| --- | --- | --- |
| Registry | `8oo4J9tBB3Hna1jRQ3rWvJjojqM5DYTDJo5cejUuJy3C` | `35b146922d9a59c474b624980033221f03cf31a5403a446d8132341ccafd226a` |
| Metaplex Core | `CoREENxT6tW1HoK8ypY1SxRMZTcVPm7R94rH4PZNhX7d` | `72726e4b8fc837e9ee05d8a942903c5f10890d33cb4480344844211b30b03dcb` |

On 2026-09-20 the live read resolved public devnet asset `J9Na6oihoANLxxQAG7oQGKTzQKj7yq7WyVV96FsyiwZh` at finalized slot **501355160**, with a matching cached/current controller and no operational wallet. This is a registry example owned by another party, not an evaluated or endorsed provider. No metadata URI was fetched by that smoke test. The observed hashes pin deployment drift; they do **not** establish a reproducible source-to-binary match or independence from the selected RPC operator.

The same asset was rechecked on **2026-09-23 at 21:09:06.945 UTC**, finalized slot **503134164**. Existing deployment pins passed; cached/current controller still matched and no operational wallet was present. This remained a read-only registry check with no metadata fetch, enrollment signature, issuance or payment. The [owned-identity provider acceptance](provider-enrollment.md#remaining-acceptance) is still pending.

Current Core ownership takes precedence over the registry's cached owner. After an external transfer, a stale operational wallet is disabled until ownership is synchronized. A binding from the former controller/wallet fails. A new controller can sign a new provider binding, but the issuer's evaluated-controller assertion must also match: the new owner cannot inherit the old evaluation simply by signing service metadata. The adapter supports this pinned devnet layout only. Mainnet, compressed assets and other deployment layouts remain unsupported.

```sh
pnpm consumer resolve --asset J9Na6oihoANLxxQAG7oQGKTzQKj7yq7WyVV96FsyiwZh
pnpm consumer metrics
```

## Measurements and decisions

The `core.*.v1` metric catalog maps exact source-report JSON pointers, dimension IDs and units under `passport-interpretation/0.2.0`. It never uses display labels as keys. It exposes eight current measurements: numeric prior/evidence weights, numeric reference RMSE/Brier, discovery Brier, derived/provenance update sizes and decision/report agreement. The [investigation adapter](investigation-passport.md) adds 14 `investigation.*.v1` observations and coverage counts under `passport-interpretation/0.3.0`, supporting discovery mode only for current policies. Model coefficients are excluded. Existing passport bytes are not rewritten. Missing, ambiguous or unsupported mappings return review.

A policy chooses a point estimate or requires the entire 95% interval to lie within its bounds. Missing required intervals return review; failed bounds return ineligible. These are task-specific buyer rules, not an overall cognitive score. Requiring verified execution or predictive validation returns review because the current core attestation supports neither. Synthetic or unspecified origin is ineligible. Provisional evidence must be explicitly accepted.

Decisions bind exact request and policy file bytes, including whitespace, plus the passport, attestation, signed provider binding, latest status and registry snapshot. Expiry is the earliest applicable attestation/binding/status/freshness/receipt bound. **Decision JSON is an unsigned local result, not a bearer authorization.** `matchesReceipt` only checks scope on an already trusted in-process result; it does not authenticate a result received from another party. Re-resolve and re-evaluate before purchasing. A later payment implementation must verify the actual body digest and x402 terms, preserve the nonce/order binding and require explicit payment authorization.

## Status and private retrieval

Issuer status consists of sequential signed events. The first event adds the issuer's evaluated-controller assertion to the unchanged passport attestation; that controller cannot change within its history. Issuers must establish that association before publication; it remains an issuer assertion, not execution attestation. Withdrawn and corrected states cannot return to active or silently change their correction target. Corrections require a different attestation digest and a new decision. Events are published atomically without replacing an existing file; exclusive writer locks protect concurrent appends. A crash-held lock requires operator inspection. This filesystem store is a local prototype, not a multi-tenant availability or transparency service.

The consumer fetches the full history and checks issuer, target, signatures, sequence, chronology, predecessor links, latest validity and maximum age. The CLI persists the newest sequence/hash for each attestation, rejecting older histories or a conflicting prefix. A fresh consumer cannot detect an unseen newer withdrawal within the allowed freshness window. An issuer can still withhold publication; signatures alone do not provide globally witnessed status. Missing or stale required status returns review.

Retrieval uses explicit operator-configured origin allowlists, bounded response sizes/timeouts and no redirects. Only HTTPS is accepted outside an explicitly enabled loopback preview. Origin-scoped bearer capabilities are never forwarded across redirects. The local artifact server serves only explicitly mapped files plus the selected issuer's status directory, requires a bearer capability, and sends `no-store`. It does not expose a source-report directory or evaluation database. DNS/egress policy for trusted hosted origins, tenant isolation, public hosting and long-term availability remain deployment work.

For a private preview, an explicit `loopbackMirrors` map can retrieve an HTTPS-named artifact from a local server while its signed URI stays unchanged. The target must be an allowed loopback origin. This is local retrieval, not evidence that the public HTTPS address hosts the artifact.

## Operator commands

First derive and verify a completed agent passport, then create its existing issuer attestation using `passport-record`. Keep reports, keys, capabilities and generated outputs outside Git. All output artifact writes refuse overwrites.

```sh
# Provider supplies the complete provider-binding.v1 payload; sign with current authority.
pnpm consumer bind --payload output/provider-binding-payload.json --keypair PRIVATE_KEYPAIR --output output/provider-binding.json

# Issuer publishes initial active status, then refreshes or appends withdrawal/correction events.
pnpm consumer status --keypair ISSUER_KEYPAIR --controller EVALUATED_CONTROLLER --status-root output/issuer-status --attestation ATTESTATION_DIGEST --status active --reason 'Initial issuance' --expires CANONICAL_UTC_TIMESTAMP

# Manifest is a route-to-file object, paths relative to its own directory.
# Example: {"/passport.json":"passport.json","/attestation.json":"attestation.json","/binding.json":"provider-binding.json"}
pnpm consumer serve --artifacts output/artifacts.json --token-file output/artifact-token --status-root output/issuer-status --issuer ISSUER_PUBLIC_KEY

# Buyer supplies the policy, exact service request, retrieval config and persistent status cache.
pnpm consumer decide --asset AGENT_ASSET --binding-uri HTTPS_BINDING_URI --request output/request.json --policy output/policy.json --retrieval output/retrieval.json --state output/status-cache.json --output output/decision.json
```

Retrieval config fields are `allowedOrigins`, optional `bearerByOrigin`, `maxBytes`, `timeoutMs`, and, for previews, `allowLoopbackHttp`/`loopbackMirrors`. Store capability-bearing configuration privately. Status and decision-cache locks are intentionally not removed by a second process; inspect an interrupted operation before removing its stale lock.

The complete offline demonstration is `pnpm --filter @epistemics/solana exec node --import tsx --test test/consumer.test.ts`. It covers acceptance with invented agent-origin contract fixtures, synthetic-origin rejection, ownership transfer, deployment drift, subject/payee/configuration substitutions, status unavailability/rollback/withdrawal/correction, byte tampering, uncertainty requirements and private HTTP limits. All fixture identity observations are explicitly `simulation`; none is evidence of real-agent measurement or live-chain execution.
