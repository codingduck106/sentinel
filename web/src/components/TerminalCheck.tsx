"use client";

import { useEffect, useState } from "react";
import type { AnalyzeResult, TacticId } from "@/lib/api";
import { EXAMPLES, MAX_CHARS, useCheck } from "@/lib/useCheck";
import { AiOptIn } from "./AiOptIn";
import { Results } from "./Results";

type Line =
  | { kind: "info"; text: string }
  | { kind: "flag"; tactic: TacticId; name: string; quotes: string[] }
  | { kind: "verdict"; level: AnalyzeResult["risk_level"]; text: string };

const LEVEL = { low: "Low risk", medium: "Medium risk", high: "High risk" } as const;

/** Distinct evidence quotes, longest first, dropping ones contained in another (e.g. "HSBC" inside "HSBC:"). */
function quotes(evidence: { text: string }[], max = 2): string[] {
  const out: string[] = [];
  const all = [...new Set(evidence.map((e) => e.text.trim().replace(/[:.,!]+$/, "")))].sort((a, b) => b.length - a.length);
  for (const q of all) if (!out.some((o) => o.toLowerCase().includes(q.toLowerCase()))) out.push(q);
  const order = evidence.map((e) => e.text.trim().replace(/[:.,!]+$/, ""));
  return out.sort((a, b) => order.indexOf(a) - order.indexOf(b)).slice(0, max);
}

/** The session transcript for one result: flagged phrases, the spam score, then the verdict. */
export function toLines(r: Pick<AnalyzeResult, "text" | "tactics" | "scam_probability" | "risk_level" | "verdict">): Line[] {
  const found = r.tactics.filter((t) => t.detected).sort((a, b) => b.score - a.score);
  return [
    ...(found.length
      ? found.map((t): Line => ({ kind: "flag", tactic: t.id, name: t.name, quotes: quotes(t.evidence) }))
      : [{ kind: "info", text: "No pressure tactics found" } as Line]),
    { kind: "info", text: `Spam pattern match ${Math.round(r.scam_probability * 100)}%` },
    { kind: "verdict", level: r.risk_level, text: r.verdict },
  ];
}

// Real output of /api/analyze for the bank-alert example (frozen so the page shows it before any check).
const SAMPLE_RESULT = {
  text: EXAMPLES[0].text,
  scam_probability: 0.37,
  risk_level: "high",
  verdict: "This looks like a scam",
  tactics: [
    { id: "urgency", name: "Urgency", detected: true, score: 1, what: "", advice: "", evidence: [{ cue: "", text: "within 24 hours", start: 0, end: 0 }, { cue: "", text: "verify immediately", start: 0, end: 0 }] },
    { id: "fear", name: "Fear", detected: true, score: 1, what: "", advice: "", evidence: [{ cue: "", text: "unusual activity", start: 0, end: 0 }, { cue: "", text: "will be suspended", start: 0, end: 0 }] },
    { id: "authority_impersonation", name: "Pretending to be official", detected: true, score: 1, what: "", advice: "", evidence: [{ cue: "", text: "HSBC", start: 0, end: 0 }, { cue: "", text: "We have detected", start: 0, end: 0 }] },
  ],
} satisfies Parameters<typeof toLines>[0];
const SAMPLE: Line[] = [{ kind: "info", text: "Example: the bank alert" }, ...toLines(SAMPLE_RESULT)];

function Transcript({ lines, shown }: { lines: Line[]; shown: number }) {
  return (
    <ol className="out-lines">
      {lines.slice(0, shown).map((l, i) =>
        l.kind === "info" ? (
          <li key={i} className="ln-info">{l.text}</li>
        ) : l.kind === "flag" ? (
          <li key={i} className={`ln-flag c-${l.tactic}`}>
            <span className="dot" aria-hidden />
            <span className="ln-name">{l.name}</span>
            <span className="ln-quotes">{l.quotes.map((q) => `“${q}”`).join("  ")}</span>
          </li>
        ) : (
          <li key={i} className={`ln-verdict lvl-${l.level}`}>
            <span className="ln-v">{l.text}</span>
            <span className="ln-level">{LEVEL[l.level]}</span>
          </li>
        ),
      )}
    </ol>
  );
}

/** The signature moment: the transcript prints one line at a time, ending on the verdict. Remounted per result. */
function Printer({ lines }: { lines: Line[] }) {
  const [shown, setShown] = useState(() =>
    window.matchMedia("(prefers-reduced-motion: reduce)").matches ? lines.length : 1,
  );
  useEffect(() => {
    if (shown >= lines.length) return;
    const id = window.setTimeout(() => setShown((n) => n + 1), 110);
    return () => window.clearTimeout(id);
  }, [shown, lines.length]);
  return (
    <>
      <Transcript lines={lines} shown={shown} />
      {shown >= lines.length && <a className="link" href="#result">See the highlighted message and what to do</a>}
    </>
  );
}

export function TerminalCheck() {
  const { text, setText, result, error, loading, aiConsent, setAiConsent, ai, inputRef, length, over, submit, loadExample, reset } = useCheck();
  const lines = result ? toLines(result) : null;
  return (
    <>
      <form className="term" onSubmit={submit} noValidate aria-label="Scam text checker">
        <p className="term-cmd" aria-hidden><span className="prompt">$</span> sentinel check<span className="cursor" /></p>

        <div className="term-head">
          <label htmlFor="msg" className="term-label">Paste the text you received</label>
          <div className="examples">
            <span className="soft">Or try an example:</span>
            {EXAMPLES.map((ex) => (
              <button key={ex.label} type="button" className="chip" onClick={() => loadExample(ex.text)}>{ex.label}</button>
            ))}
          </div>
        </div>
        <div className="term-input">
          <textarea
            id="msg"
            ref={inputRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste it here, links and numbers included"
            aria-describedby="counter"
            aria-invalid={over}
            autoComplete="off"
            spellCheck={false}
          />
          <span id="counter" className={`counter ${over ? "over" : ""}`} aria-live="polite">
            {length} / {MAX_CHARS}{over ? " — too long" : ""}
          </span>
        </div>


        <AiOptIn checked={aiConsent} onChange={setAiConsent} />

        <div className="term-submit">
          <button type="submit" className="btn" disabled={over || loading} aria-busy={loading}>
            {loading ? <><span className="spinner" aria-hidden />Checking…</> : "Check this message"}
          </button>
          <p className="privacy">Free. We don&rsquo;t store your messages.</p>
        </div>

        <div className="term-out" aria-live="polite">
          {error ? (
            <p className="error" role="alert">{error}</p>
          ) : lines ? (
            <Printer key={result?.text} lines={lines} />
          ) : (
            <>
              <div className="out-sample"><Transcript lines={SAMPLE} shown={SAMPLE.length} /></div>
            </>
          )}
        </div>
      </form>

      {result && <Results r={result} ai={ai} onReset={reset} scroll={false} showVerdict={false} />}
    </>
  );
}
