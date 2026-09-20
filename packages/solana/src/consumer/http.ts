import type { Account, RegistryTransport } from "./registry.js";

export interface FetchPolicy {
  allowedOrigins: string[];
  allowLoopbackHttp?: boolean;
  maxBytes?: number;
  timeoutMs?: number;
  /** Operator-supplied capabilities, sent only to an explicitly allowed origin. */
  bearerByOrigin?: Record<string, string>;
  /** Explicit local artifact mirrors for private previews; signed URIs remain unchanged. */
  loopbackMirrors?: Record<string, string>;
}

export function allowedUrl(value: string, policy: FetchPolicy): URL {
  const u = new URL(value);
  const local = ["127.0.0.1", "[::1]", "localhost"].includes(u.hostname);
  if (
    u.username ||
    u.password ||
    u.hash ||
    !(
      u.protocol === "https:" ||
      (policy.allowLoopbackHttp && local && u.protocol === "http:")
    ) ||
    !policy.allowedOrigins.includes(u.origin)
  )
    throw new Error("URL outside configured retrieval origins");
  return u;
}

export async function fetchBytes(
  uri: string,
  policy: FetchPolicy,
  init: RequestInit = {},
): Promise<Uint8Array> {
  const original = allowedUrl(uri, policy);
  const mirror = policy.loopbackMirrors?.[original.origin];
  let u = original;
  if (mirror) {
    const target = allowedUrl(mirror, policy);
    if (
      !policy.allowLoopbackHttp ||
      !["127.0.0.1", "[::1]", "localhost"].includes(target.hostname) ||
      target.pathname !== "/" ||
      target.search
    )
      throw new Error("Mirror must be an explicit loopback origin");
    u = new URL(original.pathname + original.search, target);
  }
  const limit = policy.maxBytes ?? 2_000_000;
  const response = await fetch(u, {
    ...init,
    headers: {
      ...init.headers,
      ...(policy.bearerByOrigin?.[u.origin]
        ? { authorization: `Bearer ${policy.bearerByOrigin[u.origin]}` }
        : {}),
    },
    redirect: "error",
    signal: AbortSignal.timeout(policy.timeoutMs ?? 15_000),
  });
  if (!response.ok || !response.body)
    throw new Error(`Artifact HTTP status ${response.status}`);
  if (Number(response.headers.get("content-length")) > limit) {
    await response.body.cancel();
    throw new Error("Artifact exceeds size limit");
  }
  const chunks: Uint8Array[] = [];
  let length = 0;
  const reader = response.body.getReader();
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      length += value.length;
      if (length > limit) throw new Error("Artifact exceeds size limit");
      chunks.push(value);
    }
  } finally {
    await reader.cancel();
  }
  return Buffer.concat(chunks, length);
}

export function parseJson(bytes: Uint8Array): unknown {
  return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
}

export function rpcTransport(rpcUrl: string): RegistryTransport {
  const policy = {
    allowedOrigins: [new URL(rpcUrl).origin],
    maxBytes: 4_000_000,
    timeoutMs: 30_000,
  };
  allowedUrl(rpcUrl, policy);
  async function call(method: string, params: unknown[]) {
    const data = parseJson(
      await fetchBytes(rpcUrl, policy, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }),
      }),
    ) as { id?: number; error?: unknown; result?: unknown };
    if (data.id !== 1 || data.error || data.result === undefined)
      throw new Error("RPC request failed");
    return data.result;
  }
  return {
    mode: "rpc_observed",
    async genesis() {
      const result = await call("getGenesisHash", []);
      if (typeof result !== "string") throw new Error("Invalid RPC genesis");
      return result;
    },
    async accounts(keys) {
      const result = (await call("getMultipleAccounts", [
        keys,
        { encoding: "base64", commitment: "finalized" },
      ])) as {
        context: { slot: number };
        value: (Account | null)[];
      };
      return { slot: result.context.slot, accounts: result.value };
    },
  };
}
