# Offline passport attestations

Implemented contract: `epistemics.passport-attestation.v1`, defined in [the JSON Schema](../schemas/passport-attestation.v1.json). This is an additive envelope for agent core passport.v2 artifacts, separate from the existing report record.v1 and its Memo format. Legacy passports and human publication are not supported by this signer.

The issuer signs the exact passport digest, source-report digest, subject/configuration, protocol, evaluator and interpretation versions, response origin, URI and validity window. It attests to a provisional profile. The underlying profile retains `issuance_status="draft_unsigned"`: that describes the unsigned document itself, while the detached envelope carries the signature. Neither file is rewritten to claim stronger measurement coverage. Synthetic and unspecified origins remain explicit.

All signed payload fields are strings. Sort property names in UTF-16 code-unit order, apply ECMAScript `JSON.stringify` without whitespace, then encode as UTF-8. Unknown fields are rejected. The attestation digest is SHA-256 of those canonical payload bytes. Ed25519 signs:

```text
UTF8("epistemics/passport-attestation-signature/v1\n") || canonical_payload_bytes
```

This restricted encoding is not a general JSON canonicalization standard. Passport and report digests bind exact original file bytes, including trailing newlines. The envelope itself can be reformatted without changing the signature. It has no chain/network field because offline verification is chain-independent; a future registry association must bind chain, program and agent asset explicitly.

## Usage

Start with a completed agent core report and its passport saved from the shared service. First verify deterministic derivation in Python:

```sh
uv run epistemics passport verify output/core-passport.json --report output/core-report.json

# Offline demonstration; prints an ephemeral issuer public key.
pnpm passport-record demo --passport output/core-passport.json --report output/core-report.json --output output/passport-attestation.json

# Supply a public key obtained through a trusted channel, not blindly from the envelope.
pnpm passport-record verify --passport output/core-passport.json --attestation output/passport-attestation.json --issuer TRUSTED_ISSUER_PUBLIC_KEY --report output/core-report.json
```

`create` uses `--keypair PATH --uri URI --expires YYYY-MM-DDTHH:mm:ss.sssZ` in place of the demo defaults. It requires `--report` and `--output`. The demo expires after one day; real issuance requires an explicit expiry. Every write refuses to overwrite an existing file. No URI is fetched, uploaded or advertised, no identity is registered and no transaction is sent. The keypair is a local Solana CLI-format file and must remain outside Git.

The TypeScript signer validates JSON schemas, completion/participant constraints, report hash and matching session context. It does not recompute the behavioral measurements or deterministic Python derivation. Operators should run the Python derivation check before issuance. The verifier always checks the envelope, signature, expected issuer, exact passport bytes, bound metadata and time window. Source-report validation is optional at verification because that report can remain private.

Machine output explicitly reports `report_bytes_checked`, `derivation_recomputed`, `registry_binding_verified`, `execution_verified`, `revocation_checked` and `payment_authorized`. Only the first can currently be true. `verified_offline` means the signature, bytes and validity window passed against the supplied issuer key; it is not a hiring or payment decision. This version only supports `execution_verification="operator_asserted"`.

Expiry is an issuer validity bound, not proof of freshness. Consumers must separately inspect evaluation completion time and current configuration. This offline command does not check withdrawal status. The separate [machine consumer](machine-consumer.md) now adds pinned devnet identity resolution, signed lifecycle status, private retrieval and task policy before any payment integration. Its additional contracts leave this envelope unchanged.

Tests use an actual synthetic Python core session, cross-language schema validation, ephemeral keys, tampered bytes/metadata, issuer mismatch, validity boundaries and CLI behavior. They make no registry, validator, facilitator or live-chain calls. Experimental behavior and report/passport schemas are unchanged, so this increment does not change battery/evaluator versions or require new parameter recovery.
