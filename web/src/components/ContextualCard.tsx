import type { ContextualState } from "@/lib/api";

const TACTIC_NAMES: Record<string, string> = {
  urgency: "Urgency", fear: "Fear", authority: "Pretending to be official", reward: "Too-good-to-be-true reward",
  secrecy: "Asking for secrecy", trust_building: "Building false trust", payment_redirect: "Asking for money",
  lookalike_link: "Look-alike link",
};
const SENSITIVE_NAMES: Record<string, string> = {
  otp_code: "a one-time code", password_pin: "a password or PIN", card_details: "card details",
  bank_login: "bank login details", personal_id: "personal ID details", remote_access: "remote access to a device",
  payment: "money",
};
const UNAVAILABLE: Record<string, string> = {
  daily_limit: "The AI explanation has reached today's limit.",
  busy: "The AI service is busy right now.",
  timeout: "The AI service took too long to answer.",
  refused: "The AI service declined to analyse this message.",
  invalid: "The AI's answer didn't pass our checks, so we're not showing it.",
  disabled: "The AI explanation is switched off at the moment.",
};

/** Informational only: rendered separately from, and never feeding into, the risk rating. */
export function ContextualCard({ ai, classifierRiskLevel }: { ai: ContextualState; classifierRiskLevel: "low" | "medium" | "high" }) {
  const additionalWarning =
    ai.status === "ok" &&
    classifierRiskLevel === "low" &&
    (ai.analysis.implicit_tactics.length > 0 || ai.analysis.sensitive_requests.length > 0);

  return (
    <section className="block ai-card" aria-labelledby="ai-h" aria-busy={ai.status === "loading"} data-testid="ai-card">
      <h3 id="ai-h">AI explanation</h3>
      <p className="ai-note">Written by Claude, an AI from Anthropic. For extra context only: it doesn&rsquo;t change the risk rating above, and it can be wrong.</p>

      {ai.status === "loading" && <p className="soft"><span className="spinner" aria-hidden /> Asking Claude…</p>}

      {ai.status === "unavailable" && (
        <p className="soft">
          {UNAVAILABLE[ai.reason] ?? "The AI explanation isn't available right now."} Your result above is complete.
        </p>
      )}

      {ai.status === "ok" && (
        <div className="ai-body">
          {additionalWarning && (
            <div className="ai-warning" role="note" data-testid="ai-additional-warning">
              <strong>Additional warning detected by AI</strong>
              <span>
                The original classifier result remains <strong>Low risk</strong>. This separate AI finding is informational and does not change that rating.
              </span>
            </div>
          )}
          <p className="ai-summary">{ai.analysis.intent_summary}</p>
          {ai.analysis.sensitive_requests.length > 0 && (
            <p className="ai-ask">
              <strong>It asks for {[...new Set(ai.analysis.sensitive_requests.map((s) => SENSITIVE_NAMES[s.kind] ?? s.kind))].join(", ")}.</strong>{" "}
              Scam texts often ask for this. Check with the sender another way first.
            </p>
          )}
          {ai.analysis.implicit_tactics.length > 0 && (
            <ul className="ai-tactics">
              {ai.analysis.implicit_tactics.map((t, i) => (
                <li key={i}>
                  <span className="ai-tag">{TACTIC_NAMES[t.type] ?? t.type}</span> &ldquo;{t.quote}&rdquo;
                  <span className="soft"> — {t.why}</span>
                </li>
              ))}
            </ul>
          )}
          <p>{ai.analysis.explanation}</p>
          {ai.analysis.safe_next_steps.length > 0 && (
            <ul className="steps ai-steps">{ai.analysis.safe_next_steps.map((s, i) => <li key={i}>{s}</li>)}</ul>
          )}
          {ai.redacted && <p className="soft ai-fine">Numbers and email addresses were removed before the message was sent to the AI.</p>}
        </div>
      )}
    </section>
  );
}
