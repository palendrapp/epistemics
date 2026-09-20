import { timingSafeEqual } from "node:crypto";
import { createServer } from "node:http";
import { readStatusHistory } from "./status.js";

export interface ArtifactHost {
  /** Explicit selected passport/envelope files only; never a filesystem web root. */
  artifacts: Map<string, Uint8Array>;
  token: string;
  statusRoot?: string;
  issuer?: string;
}

/** Local private retrieval demo. Production TLS, tenants and deployment are separate. */
export function artifactServer(options: ArtifactHost) {
  if (options.token.length < 32)
    throw new Error("At least 32 characters of bearer capability required");
  for (const route of options.artifacts.keys())
    if (!/^\/[a-zA-Z0-9._-]+\.json$/.test(route))
      throw new Error("Invalid artifact route");
  return createServer(async (req, res) => {
    res.setHeader("cache-control", "no-store");
    res.setHeader("x-content-type-options", "nosniff");
    const expected = Buffer.from(`Bearer ${options.token}`);
    const supplied = Buffer.from(req.headers.authorization ?? "");
    if (
      supplied.length !== expected.length ||
      !timingSafeEqual(supplied, expected)
    ) {
      res.writeHead(401).end();
      return;
    }
    if (req.method !== "GET") {
      res.writeHead(405).end();
      return;
    }
    const route = req.url ?? "";
    let bytes = options.artifacts.get(route);
    try {
      const match = /^\/status\/([0-9a-f]{64})\.json$/.exec(route);
      if (match && options.statusRoot && options.issuer) {
        const history = await readStatusHistory(
          options.statusRoot,
          options.issuer,
          match[1]!,
        );
        if (history.length) bytes = Buffer.from(`${JSON.stringify(history)}\n`);
      }
      if (!bytes) {
        res.writeHead(404).end();
        return;
      }
      res.setHeader("content-type", "application/json");
      res.writeHead(200).end(bytes);
    } catch {
      res.writeHead(503).end();
    }
  });
}
