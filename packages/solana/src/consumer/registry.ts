import {
  address,
  getAddressDecoder,
  getAddressEncoder,
  getProgramDerivedAddress,
} from "@solana/kit";
import { sha256 } from "../records.js";
import { DEVNET_GENESIS } from "../solana.js";

export const REGISTRY_PROGRAM = "8oo4J9tBB3Hna1jRQ3rWvJjojqM5DYTDJo5cejUuJy3C";
export const CORE_PROGRAM = "CoREENxT6tW1HoK8ypY1SxRMZTcVPm7R94rH4PZNhX7d";
const LOADER = "BPFLoaderUpgradeab1e11111111111111111111111";
export const NETWORK = `solana:${DEVNET_GENESIS.slice(0, 32)}`;

export interface DeploymentPin {
  genesis_hash: string;
  registry: {
    program: string;
    program_data: string;
    program_data_sha256: string;
    upgrade_authority: string;
  };
  core: {
    program: string;
    program_data: string;
    program_data_sha256: string;
    upgrade_authority: string;
  };
  sdk_revision: string;
  program_revision: string;
  idl_sha256: string;
  core_revision: string;
}

// Read-only pin observed on devnet 2026-09-20. Hashes bind entire ProgramData accounts.
// These are drift pins, not reproducible-build verification of the deployed binaries.
export const DEPLOYMENT = {
  genesis_hash: DEVNET_GENESIS,
  registry: {
    program: REGISTRY_PROGRAM,
    program_data: "FQoUY67zsXc3NnJjGGnPb4WDZPgKLHhm288nSqBrYojV",
    program_data_sha256:
      "35b146922d9a59c474b624980033221f03cf31a5403a446d8132341ccafd226a",
    upgrade_authority: "2KmHw8VbShuz9xfj3ecEjBM5nPKR5BcYHRDSFfK1286t",
  },
  core: {
    program: CORE_PROGRAM,
    program_data: "9ZC25KLUrfgSoFVgjE1rrydZBbZns58UXi8A8ZhTdGfr",
    program_data_sha256:
      "72726e4b8fc837e9ee05d8a942903c5f10890d33cb4480344844211b30b03dcb",
    upgrade_authority: "Fsxr5WVKZZoeb7xgwTWRHymSRVGY9vk7m5B5GPu1KU59",
  },
  sdk_revision: "67a896a6a871ca333c59b99fd73882d07d659959",
  program_revision: "6b344c9c71871daa35f649a6260e180be33c6810",
  idl_sha256:
    "b5109accd8efb8bb8a35121fc9108a1aaefcd096401a9a65e6003720c99bdeb1",
  core_revision: "e72d63e4118a0a95ac9b40221e81b19d49e1e102",
} as const;

export interface Account {
  owner: string;
  executable: boolean;
  data: [string, "base64"];
}
export interface RegistryTransport {
  mode: "rpc_observed" | "simulation";
  genesis(): Promise<string>;
  accounts(
    keys: string[],
  ): Promise<{ slot: number; accounts: (Account | null)[] }>;
}
export interface RegistryIdentity {
  mode: RegistryTransport["mode"];
  genesis_hash: string;
  registry_program: string;
  agent_asset: string;
  agent_pda: string;
  subject_agent_id: string;
  controller: string;
  cached_controller: string;
  operational_wallet: string | null;
  metadata_uri: string;
  slot: number;
  observed_at: string;
  deployment_sha256: string;
  account_hashes: string[];
}

export function subjectId(asset: string): string {
  return `${NETWORK}/${REGISTRY_PROGRAM}/${address(asset)}`;
}

function bytes(
  account: Account | null,
  owner: string,
  executable: boolean,
): Buffer {
  if (
    !account ||
    account.owner !== owner ||
    account.executable !== executable ||
    !Array.isArray(account.data) ||
    account.data[1] !== "base64"
  )
    throw new Error(
      "Unexpected account ownership, encoding or executable flag",
    );
  const result = Buffer.from(account.data[0], "base64");
  if (result.toString("base64") !== account.data[0])
    throw new Error("Invalid account encoding");
  return result;
}

class Reader {
  offset = 0;
  constructor(readonly data: Buffer) {}
  take(n: number): Buffer {
    if (n < 0 || this.offset + n > this.data.length)
      throw new Error("Truncated account");
    const b = this.data.subarray(this.offset, this.offset + n);
    this.offset += n;
    return b;
  }
  u8(): number {
    return this.take(1)[0]!;
  }
  bool(): number {
    const n = this.u8();
    if (n > 1) throw new Error("Invalid Borsh boolean/option");
    return n;
  }
  key(): string {
    return getAddressDecoder().decode(this.take(32));
  }
  option(): string | null {
    return this.bool() ? this.key() : null;
  }
  string(limit: number): string {
    const n = this.take(4).readUInt32LE();
    if (n > limit) throw new Error("Oversized Borsh string");
    return new TextDecoder("utf-8", { fatal: true }).decode(this.take(n));
  }
}

/** Layout pinned to the reviewed IDL; unused allocated account bytes may follow. */
export function decodeAgent(data: Buffer) {
  const r = new Reader(data);
  if (!r.take(8).equals(Buffer.from([241, 119, 69, 140, 233, 9, 112, 50])))
    throw new Error("Unexpected AgentAccount discriminator");
  const collection = r.key();
  const creator = r.key();
  const owner = r.key();
  const asset = r.key();
  const bump = r.u8();
  r.bool();
  const wallet = r.option();
  r.take(120); // three digest/count pairs
  r.option();
  r.bool();
  r.bool();
  const uri = r.string(250);
  r.string(32);
  r.string(128);
  return { collection, creator, owner, asset, bump, wallet, uri };
}

export function decodeCoreOwner(data: Buffer, collection: string): string {
  const r = new Reader(data);
  if (r.u8() !== 1) throw new Error("Expected uncompressed Core AssetV1");
  const owner = r.key();
  if (r.u8() !== 2 || r.key() !== collection)
    throw new Error("Core asset is not in the registered collection");
  r.string(4096);
  r.string(4096);
  if (r.bool()) r.take(8);
  return owner;
}

function checkDeployment(
  program: Account | null,
  data: Account | null,
  pin: DeploymentPin["registry"],
) {
  const p = bytes(program, LOADER, true);
  if (
    p.length !== 36 ||
    p.readUInt32LE() !== 2 ||
    getAddressDecoder().decode(p.subarray(4)) !== pin.program_data
  )
    throw new Error("ProgramData pointer changed");
  const d = bytes(data, LOADER, false);
  if (
    d.length < 45 ||
    d.readUInt32LE() !== 3 ||
    d[12] !== 1 ||
    getAddressDecoder().decode(d.subarray(13, 45)) !== pin.upgrade_authority ||
    sha256(d) !== pin.program_data_sha256
  )
    throw new Error("Deployment changed; review and repin required");
}

export async function resolveIdentity(
  asset: string,
  transport: RegistryTransport,
  now = new Date(),
  simulationPin?: DeploymentPin,
): Promise<RegistryIdentity> {
  if (simulationPin && transport.mode !== "simulation")
    throw new Error("Custom pins are for offline simulation only");
  const deployment = simulationPin ?? DEPLOYMENT;
  address(asset);
  if ((await transport.genesis()) !== DEPLOYMENT.genesis_hash)
    throw new Error("Wrong chain genesis");
  const [pda, bump] = await getProgramDerivedAddress({
    programAddress: address(REGISTRY_PROGRAM),
    seeds: [
      new TextEncoder().encode("agent"),
      getAddressEncoder().encode(address(asset)),
    ],
  });
  // A single finalized bank snapshot for executable pins and both identity accounts.
  const result = await transport.accounts([
    REGISTRY_PROGRAM,
    deployment.registry.program_data,
    CORE_PROGRAM,
    deployment.core.program_data,
    pda,
    asset,
  ]);
  if (
    !Number.isSafeInteger(result.slot) ||
    result.slot < 0 ||
    result.accounts.length !== 6
  )
    throw new Error("Invalid RPC snapshot");
  const [program, programData, core, coreData, agentAccount, assetAccount] =
    result.accounts;
  checkDeployment(program!, programData!, deployment.registry);
  checkDeployment(core!, coreData!, deployment.core);
  const agent = decodeAgent(bytes(agentAccount!, REGISTRY_PROGRAM, false));
  if (agent.asset !== asset || agent.bump !== bump)
    throw new Error("Agent PDA/asset mismatch");
  const owner = decodeCoreOwner(
    bytes(assetAccount!, CORE_PROGRAM, false),
    agent.collection,
  );
  return {
    mode: transport.mode,
    genesis_hash: DEPLOYMENT.genesis_hash,
    registry_program: REGISTRY_PROGRAM,
    agent_asset: asset,
    agent_pda: pda,
    subject_agent_id: subjectId(asset),
    controller: owner,
    cached_controller: agent.owner,
    // A direct Core transfer can leave the cached owner and old operational wallet stale.
    operational_wallet: agent.owner === owner ? agent.wallet : null,
    metadata_uri: agent.uri,
    slot: result.slot,
    observed_at: now.toISOString(),
    deployment_sha256: sha256(JSON.stringify(deployment)),
    account_hashes: result.accounts.map((a) =>
      sha256(Buffer.from(a!.data[0], "base64")),
    ),
  };
}
