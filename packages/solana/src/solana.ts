import {
  appendTransactionMessageInstruction,
  assertIsTransactionWithinSizeLimit,
  type Blockhash,
  createClient,
  createSolanaRpc,
  createTransactionMessage,
  getBase64EncodedWireTransaction,
  getSignatureFromTransaction,
  type KeyPairSigner,
  pipe,
  setTransactionMessageFeePayerSigner,
  setTransactionMessageLifetimeUsingBlockhash,
  signature,
  signTransactionMessageWithSigners,
} from "@solana/kit";
import { solanaRpc } from "@solana/kit-plugin-rpc";
import {
  getAddMemoInstruction,
  MEMO_PROGRAM_ADDRESS,
  memoProgram,
} from "@solana-program/memo";
import { memoText, type SignedRecord, verifyRecord } from "./records.js";

export const DEVNET_GENESIS = "EtWTRABZaYq6iMfeYKouRu166VU2xqa1wcaWoxPkrZBG";
export const DEFAULT_RPC = "https://api.devnet.solana.com";

export function assertDevnet(genesis: string): void {
  if (genesis !== DEVNET_GENESIS)
    throw new Error("This MVP accepts Solana devnet only");
}

export async function buildAnchorTransaction(
  record: SignedRecord,
  signer: KeyPairSigner,
  lifetime: { blockhash: Blockhash; lastValidBlockHeight: bigint },
) {
  await verifyRecord(record);
  if (record.payload.issuer !== signer.address)
    throw new Error("Anchor signer must be the record issuer");
  const message = pipe(
    createTransactionMessage({ version: 0 }),
    (m) => setTransactionMessageFeePayerSigner(signer, m),
    (m) => setTransactionMessageLifetimeUsingBlockhash(lifetime, m),
    (m) =>
      appendTransactionMessageInstruction(
        getAddMemoInstruction({ memo: memoText(record), signers: [signer] }),
        m,
      ),
  );
  const transaction = await signTransactionMessageWithSigners(message);
  assertIsTransactionWithinSizeLimit(transaction);
  return transaction;
}

/** Network IO is explicit; preview simulates a signed transaction and never submits it. */
export async function anchorRecord(
  record: SignedRecord,
  reportBytes: Uint8Array,
  signer: KeyPairSigner,
  rpcUrl = DEFAULT_RPC,
  submit = false,
) {
  await verifyRecord(record, reportBytes);
  const client = createClient({ payer: signer })
    .use(solanaRpc({ rpcUrl }))
    .use(memoProgram());
  const abortSignal = AbortSignal.timeout(30_000);
  assertDevnet(await client.rpc.getGenesisHash().send({ abortSignal }));
  const { value: lifetime } = await client.rpc
    .getLatestBlockhash({ commitment: "confirmed" })
    .send({ abortSignal });
  const transaction = await buildAnchorTransaction(record, signer, lifetime);
  const wire = getBase64EncodedWireTransaction(transaction);
  const simulation = await client.rpc
    .simulateTransaction(wire, {
      encoding: "base64",
      sigVerify: true,
      commitment: "confirmed",
    })
    .send({ abortSignal });
  if (simulation.value.err !== null) {
    throw new Error(
      `Simulation failed: ${JSON.stringify(simulation.value.err)}`,
    );
  }
  const txSignature = getSignatureFromTransaction(transaction);
  if (!submit)
    return {
      status: "simulated",
      signature: txSignature,
      memo: memoText(record),
    };
  try {
    const sent = await client.rpc
      .sendTransaction(wire, {
        encoding: "base64",
        skipPreflight: false,
        preflightCommitment: "confirmed",
        maxRetries: 3n,
      })
      .send({ abortSignal });
    if (sent !== txSignature)
      throw new Error("RPC returned an unexpected signature");
  } catch (error) {
    // Preserve the locally known signature even if the network acknowledgement is lost.
    throw new Error(
      `Submission outcome unknown. Check transaction ${txSignature} before retrying.`,
      { cause: error },
    );
  }
  // Submission is not finality. The CLI returns a receipt that can be checked independently.
  return {
    status: "submitted",
    signature: txSignature,
    memo: memoText(record),
    explorer: `https://explorer.solana.com/tx/${txSignature}?cluster=devnet`,
  };
}

export interface ParsedTransaction {
  meta: { err: unknown } | null;
  transaction: {
    message: {
      accountKeys: readonly { pubkey: string; signer: boolean }[];
      instructions: readonly { programId: string; parsed?: unknown }[];
    };
  };
}

/** Only the actual Memo program instruction counts; arbitrary program logs do not. */
export function assertAnchorIncluded(
  record: SignedRecord,
  tx: ParsedTransaction | null,
): void {
  if (!tx?.meta || tx.meta.err !== null)
    throw new Error("Transaction missing or unsuccessful");
  const message = tx.transaction.message;
  if (
    !message.accountKeys.some(
      (k) => k.signer && k.pubkey === record.payload.issuer,
    )
  ) {
    throw new Error("Record issuer did not sign the transaction");
  }
  if (
    !message.instructions.some(
      (i) =>
        i.programId === MEMO_PROGRAM_ADDRESS && i.parsed === memoText(record),
    )
  ) {
    throw new Error("Expected Memo commitment not found");
  }
}

export async function verifyAnchor(
  record: SignedRecord,
  txSignature: string,
  rpcUrl = DEFAULT_RPC,
) {
  await verifyRecord(record);
  const rpc = createSolanaRpc(rpcUrl);
  const abortSignal = AbortSignal.timeout(30_000);
  assertDevnet(await rpc.getGenesisHash().send({ abortSignal }));
  const tx = await rpc
    .getTransaction(signature(txSignature), {
      commitment: "finalized",
      encoding: "jsonParsed",
      maxSupportedTransactionVersion: 0,
    })
    .send({ abortSignal });
  assertAnchorIncluded(record, tx);
  return {
    status: "finalized",
    signature: txSignature,
    record_sha256: record.record_sha256,
  };
}
