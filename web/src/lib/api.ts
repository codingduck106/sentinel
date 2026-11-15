export type TacticId = "urgency" | "fear" | "authority_impersonation" | "reward";

export interface Evidence { cue: string; text: string; start: number; end: number }

export interface Tactic {
  id: TacticId;
  name: string;
  detected: boolean;
  score: number;
  what: string;
  advice: string;
  evidence: Evidence[];
}

export interface AnalyzeResult {
  text: string;
  verdict: string;
  risk_level: "low" | "medium" | "high";
  risk_score: number;
  scam_probability: number;
  classifier_label: "spam" | "legitimate";
  tactics: Tactic[];
  tactics_detected: TacticId[];
  advice: string;
}

export const MAX_CHARS = 2000;

export class AnalyzeError extends Error {}

export async function analyzeMessage(text: string, signal?: AbortSignal): Promise<AnalyzeResult> {
  let res: Response;
  try {
    res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text }),
      signal,
    });
  } catch (e) {
    if ((e as Error).name === "AbortError") throw e;
    throw new AnalyzeError("Couldn't reach Sentinel. Check your connection and try again.");
  }
  if (res.status === 422 || res.status === 413) {
    throw new AnalyzeError(`Paste a message between 1 and ${MAX_CHARS} characters long.`);
  }
  if (res.status === 429) {
    throw new AnalyzeError("Too many checks in a short time. Wait a minute and try again.");
  }
  if (!res.ok) {
    throw new AnalyzeError("Sentinel couldn't check this message right now. Try again in a moment.");
  }
  return (await res.json()) as AnalyzeResult;
}

// ---- Opt-in AI context (informational only; never affects the risk rating) ----
export interface AIAnalysis {
  intent_summary: string;
  implicit_tactics: { type: string; quote: string; why: string }[];
  sensitive_requests: { kind: string; quote: string }[];
  explanation: string;
  safe_next_steps: string[];
}

export type ContextualState =
  | { status: "loading" }
  | { status: "ok"; model: string; analysis: AIAnalysis; redacted: boolean }
  | { status: "unavailable"; reason: string };

/** Never throws (except on abort): every failure becomes an "unavailable" card. */
export async function fetchContextual(text: string, signal?: AbortSignal): Promise<ContextualState> {
  try {
    const res = await fetch("/api/contextual", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text, consent: true }),
      signal,
    });
    if (!res.ok) return { status: "unavailable", reason: res.status === 429 ? "busy" : "error" };
    const body = await res.json();
    if (body?.status === "ok" && body.analysis) return body as ContextualState;
    return { status: "unavailable", reason: typeof body?.reason === "string" ? body.reason : "error" };
  } catch (e) {
    if ((e as Error).name === "AbortError") throw e;
    return { status: "unavailable", reason: "error" };
  }
}
