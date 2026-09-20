import { randomBytes } from "node:crypto";
import {
  mkdir,
  open,
  readFile,
  rename,
  unlink,
  writeFile,
} from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { parseArgs } from "node:util";
import type { ProviderBinding } from "./consumer/contracts.js";
import { createProviderBinding, evaluate } from "./consumer/evaluate.js";
import { artifactServer } from "./consumer/hosting.js";
import { type FetchPolicy, rpcTransport } from "./consumer/http.js";
import { METRIC_CATALOG } from "./consumer/metrics.js";
import { resolveIdentity } from "./consumer/registry.js";
import {
  appendStatus,
  createStatus,
  readStatusHistory,
} from "./consumer/status.js";
import { loadSigner } from "./records.js";

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    asset: { type: "string" },
    rpc: { type: "string", default: "https://api.devnet.solana.com" },
    request: { type: "string" },
    policy: { type: "string" },
    retrieval: { type: "string" },
    "binding-uri": { type: "string" },
    state: { type: "string" },
    output: { type: "string" },
    payload: { type: "string" },
    keypair: { type: "string" },
    attestation: { type: "string" },
    "status-root": { type: "string" },
    status: { type: "string" },
    reason: { type: "string" },
    replacement: { type: "string", default: "" },
    expires: { type: "string" },
    artifacts: { type: "string" },
    "token-file": { type: "string" },
    issuer: { type: "string" },
    controller: { type: "string" },
    port: { type: "string", default: "8788" },
  },
});
function required(name: keyof typeof values): string {
  const result = values[name];
  if (!result) throw new Error(`--${name} is required`);
  return result;
}
async function readJson(path: string): Promise<unknown> {
  return JSON.parse(await readFile(resolve(path), "utf8"));
}
async function save(path: string, value: unknown) {
  const destination = resolve(path);
  await mkdir(dirname(destination), { recursive: true });
  await writeFile(destination, `${JSON.stringify(value, null, 2)}\n`, {
    flag: "wx",
    mode: 0o600,
  });
}

async function main() {
  if (positionals.length !== 1)
    throw new Error("Choose resolve, decide, bind, status, serve or metrics");
  const command = positionals[0];
  if (command === "metrics") return METRIC_CATALOG;
  if (command === "resolve")
    return resolveIdentity(required("asset"), rpcTransport(required("rpc")));
  if (command === "bind") {
    const payload = (await readJson(required("payload"))) as ProviderBinding;
    const signed = await createProviderBinding(
      payload,
      await loadSigner(required("keypair")),
    );
    await save(required("output"), signed);
    return {
      status: "signed_provider_binding",
      payload_sha256: signed.payload_sha256,
    };
  }
  if (command === "status") {
    const issuer = await loadSigner(required("keypair"));
    const digest = required("attestation");
    const root = resolve(required("status-root"));
    const history = await readStatusHistory(root, issuer.address, digest);
    const status = required("status");
    if (!["active", "withdrawn", "corrected"].includes(status))
      throw new Error("Unknown status");
    const event = await createStatus(history, issuer, digest, {
      evaluated_controller:
        values.controller ??
        history[0]?.payload.evaluated_controller ??
        required("controller"),
      status: status as "active" | "withdrawn" | "corrected",
      replacement_attestation_sha256: values.replacement!,
      reason: required("reason"),
      issued_at: new Date().toISOString(),
      expires_at: required("expires"),
    });
    await appendStatus(root, event);
    return {
      status: "appended",
      sequence: event.payload.sequence,
      payload_sha256: event.payload_sha256,
    };
  }
  if (command === "decide") {
    // Serialize local cache updates and decisions so parallel calls cannot lose a newer status.
    const statePath = resolve(required("state"));
    await mkdir(dirname(statePath), { recursive: true, mode: 0o700 });
    const lockPath = `${statePath}.lock`;
    const lock = await open(lockPath, "wx", 0o600);
    try {
      let remembered: Record<string, { sequence: string; sha256: string }> = {};
      try {
        remembered = (await readJson(statePath)) as typeof remembered;
      } catch (e) {
        if ((e as NodeJS.ErrnoException).code !== "ENOENT") throw e;
      }
      if (
        !remembered ||
        Array.isArray(remembered) ||
        typeof remembered !== "object" ||
        Object.entries(remembered).some(
          ([k, v]) =>
            !/^[0-9a-f]{64}$/.test(k) ||
            !v ||
            !/^(0|[1-9][0-9]*)$/.test(v.sequence) ||
            !/^[0-9a-f]{64}$/.test(v.sha256),
        )
      )
        throw new Error("Invalid remembered status cache");
      const result = await evaluate({
        requestBytes: await readFile(required("request")),
        policyBytes: await readFile(required("policy")),
        agentAsset: required("asset"),
        transport: rpcTransport(required("rpc")),
        retrieval: (await readJson(required("retrieval"))) as FetchPolicy,
        rememberedStatus: remembered,
        ...(values["binding-uri"] ? { bindingUri: values["binding-uri"] } : {}),
      });
      if (
        result.attestation_sha256 &&
        result.status_sequence !== null &&
        result.status_sha256
      ) {
        remembered[result.attestation_sha256] = {
          sequence: result.status_sequence,
          sha256: result.status_sha256,
        };
        const temporary = `${statePath}.${randomBytes(8).toString("hex")}.tmp`;
        const file = await open(temporary, "wx", 0o600);
        try {
          await file.writeFile(`${JSON.stringify(remembered)}\n`);
          await file.sync();
        } finally {
          await file.close();
        }
        await rename(temporary, statePath);
        const directory = await open(dirname(statePath), "r");
        try {
          await directory.sync();
        } finally {
          await directory.close();
        }
      }
      if (values.output) await save(values.output, result);
      return result;
    } finally {
      await lock.close();
      await unlink(lockPath);
    }
  }
  if (command === "serve") {
    const manifestPath = resolve(required("artifacts"));
    const manifest = await readJson(manifestPath);
    if (!manifest || typeof manifest !== "object" || Array.isArray(manifest))
      throw new Error("Expected route-to-file object");
    const artifacts = new Map<string, Uint8Array>();
    for (const [route, file] of Object.entries(manifest)) {
      if (typeof file !== "string") throw new Error("Invalid artifact file");
      artifacts.set(
        route,
        await readFile(resolve(dirname(manifestPath), file)),
      );
    }
    const tokenPath = resolve(required("token-file"));
    await mkdir(dirname(tokenPath), { recursive: true, mode: 0o700 });
    let token;
    try {
      token = (await readFile(tokenPath, "utf8")).trim();
    } catch (e) {
      if ((e as NodeJS.ErrnoException).code !== "ENOENT") throw e;
      token = randomBytes(32).toString("hex");
      await writeFile(tokenPath, `${token}\n`, { flag: "wx", mode: 0o600 });
    }
    const port = Number(required("port"));
    if (!Number.isInteger(port) || port < 0 || port > 65535)
      throw new Error("Invalid port");
    const server = artifactServer({
      artifacts,
      token,
      ...(values["status-root"]
        ? { statusRoot: resolve(values["status-root"]) }
        : {}),
      ...(values.issuer ? { issuer: values.issuer } : {}),
    });
    await new Promise<void>((resolve, reject) => {
      server.once("error", reject);
      server.listen(port, "127.0.0.1", resolve);
    });
    return {
      status: "serving_private_loopback",
      url: `http://127.0.0.1:${(server.address() as { port: number }).port}`,
      token_file: tokenPath,
    };
  }
  throw new Error(
    "Usage: pnpm consumer <resolve|decide|bind|status|serve|metrics>; see docs/machine-consumer.md",
  );
}
main()
  .then((value) => console.log(JSON.stringify(value, null, 2)))
  .catch((e: unknown) => {
    console.error(e instanceof Error ? e.message : "Consumer operation failed");
    process.exitCode = 1;
  });
