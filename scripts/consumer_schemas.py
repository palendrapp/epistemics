"""Generate the additive TypeScript consumer contracts (no evaluation changes)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = {"type": "string", "minLength": 1, "maxLength": 4096}
D = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
OPTIONAL_D = {"type": "string", "pattern": "^([0-9a-f]{64})?$"}
AMOUNT = {"type": "string", "pattern": "^(0|[1-9][0-9]{0,39})$"}
DATE = {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"}
B = {"type": "boolean"}
N = {"type": "number"}
NULL = {"type": "null"}


def obj(fields):
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(fields),
        "properties": fields,
    }


def arr(items, minimum=0, maximum=100):
    return {"type": "array", "items": items, "minItems": minimum, "maxItems": maximum}


def enum(*values):
    return {"type": "string", "enum": list(values)}


def nullable(value):
    return {"anyOf": [value, NULL]}


def write(name, fields, signed=False):
    contract = obj({"schema_version": {"const": f"epistemics.{name}.v1"}, **fields})
    if signed:
        contract = obj({"payload": contract, "payload_sha256": D, "signature_base64": S})
    contract = {"$schema": "https://json-schema.org/draft/2020-12/schema", **contract}
    (ROOT / "schemas" / f"{name}.v1.json").write_text(json.dumps(contract, indent=2) + "\n")


write(
    "provider-enrollment",
    {
        "enrollment_id": S,
        "mode": enum("rpc_observed", "simulation"),
        **dict.fromkeys(
            [
                "genesis_hash",
                "registry_program",
                "agent_asset",
                "subject_agent_id",
                "controller",
                "signer",
                "issuer",
                "protocol_version",
            ],
            S,
        ),
        **dict.fromkeys(
            [
                "participant_sha256",
                "registry_snapshot_sha256",
                "configuration_sha256",
                "protocol_sha256",
            ],
            D,
        ),
        "issued_at": DATE,
        "expires_at": DATE,
    },
    signed=True,
)
write(
    "provider-binding",
    {
        **dict.fromkeys(
            [
                "genesis_hash",
                "registry_program",
                "agent_asset",
                "subject_agent_id",
                "controller",
                "signer",
            ],
            S,
        ),
        "configuration_sha256": D,
        "passport_sha256": D,
        **dict.fromkeys(
            [
                "passport_uri",
                "attestation_uri",
                "endpoint",
                "payee",
                "payment_network",
                "payment_asset",
            ],
            S,
        ),
        "issued_at": DATE,
        "expires_at": DATE,
    },
    signed=True,
)
write(
    "passport-status",
    {
        "issuer": S,
        "evaluated_controller": S,
        "attestation_sha256": D,
        "sequence": AMOUNT,
        "previous_sha256": OPTIONAL_D,
        "status": enum("active", "withdrawn", "corrected"),
        "replacement_attestation_sha256": OPTIONAL_D,
        "reason": S,
        "issued_at": DATE,
        "expires_at": DATE,
    },
    signed=True,
)
write(
    "consumer-request",
    {
        "subject_agent_id": S,
        "configuration_sha256": D,
        "task_id": S,
        "endpoint": S,
        "method": {"const": "POST"},
        "body_sha256": D,
        "payee": S,
        "payment_network": S,
        "payment_asset": S,
        "max_amount": AMOUNT,
        "nonce": S,
    },
)
seconds = {"type": "integer", "minimum": 1, "maximum": 31536000}
write(
    "consumer-policy",
    {
        "policy_id": S,
        "version": S,
        "task_id": S,
        "trusted_issuers": arr(obj({"issuer": S, "status_base_uri": S}), 1, 20),
        "protocol_sha256": D,
        "protocol_version": S,
        "interpretation_version": S,
        **dict.fromkeys(
            [
                "max_evaluation_age_seconds",
                "max_status_age_seconds",
                "max_binding_age_seconds",
                "receipt_ttl_seconds",
            ],
            seconds,
        ),
        "require_verified_execution": B,
        "require_predictive_validation": B,
        "allow_provisional": B,
        "measurements": arr(
            obj(
                {
                    "metric_id": S,
                    "minimum": nullable(N),
                    "maximum": nullable(N),
                    "uncertainty": enum("point", "entire_95_interval"),
                }
            ),
            1,
            30,
        ),
        "payment_network": S,
        "payment_asset": S,
        "max_amount": AMOUNT,
    },
)
interval = {"type": "array", "prefixItems": [N, N], "items": False, "minItems": 2, "maxItems": 2}
write(
    "consumer-decision",
    {
        "action": enum("eligible", "review_required", "ineligible"),
        "mode": enum("rpc_observed", "simulation"),
        "payment_authorized": {"const": False},
        "task_id": S,
        "request_sha256": D,
        "policy_sha256": D,
        **dict.fromkeys(
            [
                "passport_sha256",
                "attestation_sha256",
                "binding_sha256",
                "status_sha256",
                "registry_snapshot_sha256",
            ],
            nullable(D),
        ),
        "status_sequence": nullable(AMOUNT),
        "issued_at": DATE,
        "expires_at": DATE,
        "reasons": arr(
            obj(
                {
                    "code": S,
                    "disposition": enum("review_required", "ineligible"),
                    "detail": S,
                    "metric_id": nullable(S),
                }
            )
        ),
        "measurements": arr(
            obj(
                {
                    "metric_id": S,
                    "value": N,
                    "unit": S,
                    "interval_95": nullable(interval),
                    "evidence_pointer": S,
                    "evidence_status": S,
                }
            )
        ),
    },
)
