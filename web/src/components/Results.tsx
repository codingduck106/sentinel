"use client";

import { useEffect, useRef } from "react";
import type { AnalyzeResult, ContextualState } from "@/lib/api";
import { ContextualCard } from "./ContextualCard";
import { AnnotatedMessage } from "./AnnotatedMessage";
import { ExplanationCard } from "./ExplanationCard";
import { RiskAssessment } from "./RiskAssessment";

const SUBLINE = {
  high: (n: number) => `High risk. It uses ${words(n)} pressure tactic${n > 1 ? "s" : ""}${n === 1 ? " and its wording matches common spam texts" : ""}.`,
  medium: (n: number) => `Medium risk. ${n ? "It uses a pressure tactic that scam texts often rely on" : "The wording looks like spam texts we\u2019ve seen, but we found no pressure tactics"}. Check before you act.`,
  low: (marketing: boolean) => marketing
    ? "Low risk. This has the opt-out and offer language of a promotional message, not a scam warning."
    : "Low risk. We didn’t find pressure tactics or common spam patterns.",
};
const words = (n: number) => ["no", "one", "two", "three", "four"][n] ?? String(n);

const LEVEL_NAME = { low: "Low", medium: "Medium", high: "High" } as const;

/** Status always ships as icon + label, never colour alone (dataviz status rule). */
function StatusIcon({ level }: { level: "low" | "medium" | "high" }) {
  const common = { width: 18, height: 18, viewBox: "0 0 18 18", "aria-hidden": true as const, fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  if (level === "low") return <svg {...common}><circle cx="9" cy="9" r="7" /><path d="M5.8 9.2l2.2 2.2 4.2-4.6" /></svg>;
  if (level === "medium") return <svg {...common}><path d="M9 2.5l7 12.5H2z" /><path d="M9 7.5v3.5M9 13.2v.1" /></svg>;
  return <svg {...common}><path d="M6 1.8h6L16.2 6v6L12 16.2H6L1.8 12V6z" /><path d="M9 5.5v4.2M9 12.4v.1" /></svg>;
}

function Check() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden>
      <path d="M3.5 9.5l3.5 3.5 7.5-8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function Results({ r, ai = null, onReset, scroll = true, showVerdict = true }: { r: AnalyzeResult; ai?: ContextualState | null; onReset: () => void; scroll?: boolean; showVerdict?: boolean }) {
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    // On the homepage the terminal transcript announces the result first; the full breakdown waits below it.
    if (!scroll) return;
    ref.current?.focus();
    ref.current?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
  }, [r, scroll]);

  const detected = r.tactics.filter((t) => t.detected).sort((a, b) => b.score - a.score);
  const risky = r.risk_level !== "low";

  return (
    <section ref={ref} id="result" tabIndex={-1} className={`results lvl-${r.risk_level}`} aria-live="polite" aria-labelledby="verdict-h" data-testid="results">
      {showVerdict ? (
        <div className="verdict">
          <div>
            <h2 id="verdict-h">{r.verdict}</h2>
            <p>{r.risk_level === "low" ? SUBLINE.low(r.marketing_message) : SUBLINE[r.risk_level](detected.length)}</p>
            <p className="status"><StatusIcon level={r.risk_level} />{LEVEL_NAME[r.risk_level]} risk</p>
          </div>
        </div>
      ) : (
        // Homepage: the terminal transcript already printed the verdict; this is the breakdown under it.
        <div className="verdict">
          <div>
            <h2 id="verdict-h" className="breakdown-h">Full breakdown</h2>
            <p>{r.risk_level === "low" ? SUBLINE.low(r.marketing_message) : SUBLINE[r.risk_level](detected.length)}</p>
            <p className="status"><StatusIcon level={r.risk_level} />{LEVEL_NAME[r.risk_level]} risk</p>
          </div>
        </div>
      )}

      <RiskAssessment r={r} />

      <section className="block" aria-labelledby="msg-h">
        <h3 id="msg-h">{detected.length ? "Here’s what we spotted" : "Your message"}</h3>
        <AnnotatedMessage text={r.text} tactics={r.tactics} />
      </section>

      {detected.length > 0 && (
        <section className="block" aria-labelledby="why-h">
          <h3 id="why-h">Why it&rsquo;s worrying</h3>
          <div className="explain">
            {detected.map((t) => <ExplanationCard key={t.id} t={t} />)}
          </div>
        </section>
      )}

      {ai && <ContextualCard ai={ai} classifierRiskLevel={r.risk_level} />}

      <section className="block" aria-labelledby="next-h">
        <h3 id="next-h">{risky ? "What to do now" : "Good to know"}</h3>
        {risky ? (
          <ul className="steps">
            <li><Check />Don&rsquo;t tap any link, call any number or reply to the message.</li>
            <li><Check />Report it to your phone network. In the UK, forward it for free to 7726.</li>
            <li><Check />{r.advice}</li>
          </ul>
        ) : (
          <p className="note-card">
            Low risk isn&rsquo;t a guarantee. Scammers sometimes write like friends. If a message asks for money or codes, check with the person another way.
          </p>
        )}
      </section>

      <p className="limits">
        Sentinel analyzes message content, not the identity of its sender. A legitimate message can contain suspicious wording,
        and a sophisticated scam may contain no obvious warning signs.
      </p>

      <details className="how">
        <summary>How this was decided</summary>
        <p>
          A machine-learning model compares the wording with patterns it learned from 3,610 real UK text messages from 2011 (450 of them spam), and a separate set of rules looks for
          pressure tactics. The model learned from UK text messages and can miss newer scams, so the tactics are checked on their own.
          It can be wrong. {r.advice}
        </p>
      </details>

      <p className="again"><button type="button" className="link" onClick={onReset}>Check another message</button></p>
    </section>
  );
}
