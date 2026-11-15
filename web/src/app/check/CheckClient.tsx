"use client";

import { useEffect, useRef, useState } from "react";
import { AnalyzeError, analyzeMessage, fetchContextual, MAX_CHARS, type AnalyzeResult, type ContextualState } from "@/lib/api";
import { Results } from "@/components/Results";

const EXAMPLES: { label: string; text: string }[] = [
  { label: "Bank alert", text: "HSBC: We have detected unusual activity on your account. It will be suspended within 24 hours unless you verify immediately at hsbc-secure-check.com" },
  { label: "Prize win", text: "Congratulations! You have won a £1000 Tesco gift card. Claim now at tesco-rewards-uk.com before it expires tonight." },
  { label: "Friend’s message", text: "Hi! Running 10 mins late, grab us a table? x" },
];

export function CheckClient() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  // Opt-in AI explanation: off by default, never sent unless ticked, never affects the rating.
  const [aiConsent, setAiConsent] = useState(false);
  const [ai, setAi] = useState<ContextualState | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Count code points, like the backend (an emoji is 1 here, 2 in text.length).
  const length = [...text].length;
  const over = length > MAX_CHARS;

  // Leaving the page mid-check cancels the request.
  useEffect(() => () => abortRef.current?.abort(), []);

  /** Cancel any in-flight check so a late response can't overwrite what the user did next. */
  function cancelPending() {
    abortRef.current?.abort();
    abortRef.current = null;
    setLoading(false);
    setAi(null);
  }
  const empty = text.trim().length === 0;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (empty || over || loading) return;
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setLoading(true);
    setError(null);
    setAi(null);
    // Only when the user has opted in; runs in parallel and can never delay or alter the main result.
    if (aiConsent) {
      setAi({ status: "loading" });
      fetchContextual(text, ctrl.signal)
        .then((state) => { if (abortRef.current === ctrl) setAi(state); })
        .catch(() => { /* aborted */ });
    }
    try {
      setResult(await analyzeMessage(text, ctrl.signal));
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      setResult(null);
      setError(err instanceof AnalyzeError ? err.message : "Something went wrong. Try again.");
    } finally {
      if (abortRef.current === ctrl) setLoading(false);
    }
  }

  function reset() {
    cancelPending();
    setResult(null);
    setError(null);
    setText("");
    inputRef.current?.focus();
  }

  return (
    <>
      <h1>Check a message</h1>
      <p className="lede">Paste the text you received. Include any links or numbers exactly as they appear.</p>

      <form onSubmit={submit} noValidate>
        <div className="composer">
          <label htmlFor="msg" className="visually-hidden">Message to check</label>
          <textarea
            id="msg"
            ref={inputRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste the message here"
            aria-describedby="counter"
            aria-invalid={over}
            autoComplete="off"
            spellCheck={false}
          />
          <span id="counter" className={`counter ${over ? "over" : ""}`} aria-live="polite">
            {length} / {MAX_CHARS}{over ? " — too long" : ""}
          </span>
        </div>

        <div className="examples">
          <span className="soft">Or try an example:</span>
          {EXAMPLES.map((ex) => (
            <button key={ex.label} type="button" className="chip" onClick={() => { cancelPending(); setText(ex.text); setResult(null); setError(null); }}>
              {ex.label}
            </button>
          ))}
        </div>

        <div className="ai-optin">
          <input id="ai-optin" type="checkbox" checked={aiConsent} onChange={(e) => setAiConsent(e.target.checked)} aria-describedby="ai-optin-desc" />
          <label htmlFor="ai-optin">Also get an AI explanation (optional)</label>
          <p id="ai-optin-desc" className="soft">
            If you tick this, your message is sent to <strong>Anthropic</strong>, the company that makes the Claude AI, to write
            an extra explanation.                         Recognized digit sequences, phone/account-like numbers, email addresses, and labeled PIN/OTP/CVV codes are masked first.
            Names, postal addresses, link domains, and other words are not removed; unlabeled short numbers may remain. Veritas doesn&rsquo;t store it; Anthropic handles
            it under its <a href="https://www.anthropic.com/legal/privacy" target="_blank" rel="noopener noreferrer">privacy policy</a>.
            The AI explanation doesn&rsquo;t change the risk rating.
          </p>
        </div>

        <div className="submit-row">
          <button type="submit" className="btn" disabled={empty || over || loading} aria-busy={loading}>
            {loading ? <><span className="spinner" aria-hidden />Checking…</> : "Check this message"}
          </button>
          <p className="privacy">We don&rsquo;t store your messages. Checking takes a second{aiConsent ? "; the AI explanation a few more" : ""}.</p>
        </div>
      </form>

      {error && <p className="error" role="alert">{error}</p>}

      {result ? (
        <Results r={result} ai={ai} onReset={reset} />
      ) : (
        !error && (
          <p className="placeholder-panel">
            Your result will appear here: a verdict, the exact words that worry us, and what to do next.
          </p>
        )
      )}
    </>
  );
}
