"use client";

import { useState } from "react";
import type { AnalyzeResult, Tactic } from "@/lib/api";
import { uniquePhrases } from "@/lib/spans";

const LEVELS = ["low", "medium", "high"] as const;
const LEVEL_LABEL = { low: "Low", medium: "Medium", high: "High" };

/** Plain-language figure for a heuristic strength score (not a probability). */
export function strengthWord(t: Tactic): string {
  if (t.score === 0) return "Not found";
  if (!t.detected) return "Faint hint";
  return t.score >= 0.8 ? "Strong" : "Present";
}

/** Severity of the spam-pattern meter: the same bands the overall risk rule uses. */
function spamTone(r: AnalyzeResult): "low" | "medium" | "high" {
  if (r.classifier_label === "spam") return "high";
  return r.scam_probability >= 0.2 ? "medium" : "low";
}

/**
 * Risk assessment visualization (follows the dataviz skill):
 * - overall status scale (status colours + icon/label in the verdict),
 * - "Spam pattern match" as a meter + hero figure,
 * - "Pressure tactics" as a meter list (name · bar · figure), hover/focus tooltip per row,
 * - a table view with every value, so nothing is gated behind colour or hover.
 */
export function RiskAssessment({ r }: { r: AnalyzeResult }) {
  const [tip, setTip] = useState<string | null>(null);
  const idx = LEVELS.indexOf(r.risk_level);
  const within = Math.min(0.92, Math.max(0.08, r.risk_score * 3 - idx));
  const left = ((idx + within) / 3) * 100;
  const pct = Math.round(r.scam_probability * 100);
  const tone = spamTone(r);

  return (
    <section className="block" aria-labelledby="risk-h">
      <h3 id="risk-h">Risk assessment</h3>
      <div className="scale" role="img" aria-label={`Overall risk: ${LEVEL_LABEL[r.risk_level]}`}>
        <div className="scale-marker" style={{ left: `${left}%` }} />
        <div className="scale-track">
          {LEVELS.map((l) => <span key={l} className={l === r.risk_level ? "on" : ""} />)}
        </div>
        <div className="scale-labels" aria-hidden>
          {LEVELS.map((l) => <span key={l} className={l === r.risk_level ? "on" : ""}>{LEVEL_LABEL[l]}</span>)}
        </div>
      </div>

      <div className="signals">
        <div className="signal">
          <h4>Spam pattern match</h4>
          <p className="big">{pct}%</p>
          <div className={`meter meter-risk tone-${tone}`} role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct} aria-label="Spam pattern match">
            <span style={{ width: `${pct}%` }} />
          </div>
          <p className="caption">How closely the wording matches known spam texts.</p>
        </div>

        <div className="signal">
          <h4>Pressure tactics found</h4>
          <div className="tactic-bars" onPointerLeave={() => setTip(null)}>
            {r.tactics.map((t) => {
              const word = strengthWord(t);
              const phrases = uniquePhrases(t);
              const open = tip === t.id;
              return (
                <div
                  key={t.id}
                  className={`tactic-row c-${t.id} ${t.detected ? "on" : "off"}`}
                  tabIndex={0}
                  aria-describedby={open ? `tip-${t.id}` : undefined}
                  onPointerEnter={() => setTip(t.id)}
                  onFocus={() => setTip(t.id)}
                  onBlur={() => setTip(null)}
                >
                  <span className="name">{t.name}</span>
                  <div className="meter" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(t.score * 100)} aria-label={`${t.name} strength`}>
                    <span style={{ width: `${Math.round(t.score * 100)}%` }} />
                  </div>
                  <span className="fig">{word}</span>
                  {open && (
                    <div className="tip" role="tooltip" id={`tip-${t.id}`}>
                      <strong>{word}{t.score > 0 ? ` (${t.score.toFixed(1)} of 1)` : ""}</strong>
                      <span><span className="key" />{t.name}</span>
                      <span className="soft">
                        {phrases.length ? `Found: “${phrases.slice(0, 3).join("”, “")}”` : t.score > 0 ? "A faint cue, too weak to count on its own." : "No words for this trick in the message."}
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <p className="caption">How strongly each trick shows up in the wording.</p>
        </div>
      </div>

      <details className="numbers">
        <summary>Show these numbers as a table</summary>
        <table>
          <caption className="visually-hidden">Risk assessment values</caption>
          <thead><tr><th scope="col">Signal</th><th scope="col">Result</th><th scope="col" className="n">Value</th></tr></thead>
          <tbody>
            <tr><th scope="row">Overall risk</th><td>{LEVEL_LABEL[r.risk_level]}</td><td className="n">{r.risk_score.toFixed(2)}</td></tr>
            <tr><th scope="row">Spam pattern match</th><td>{r.classifier_label === "spam" ? "Looks like spam" : "Not clearly spam"}</td><td className="n">{pct}%</td></tr>
            {r.tactics.map((t) => (
              <tr key={t.id}><th scope="row">{t.name}</th><td>{strengthWord(t)}</td><td className="n">{t.score.toFixed(1)}</td></tr>
            ))}
          </tbody>
        </table>
      </details>
    </section>
  );
}
