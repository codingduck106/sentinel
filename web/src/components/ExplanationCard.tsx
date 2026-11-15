import type { Tactic } from "@/lib/api";
import { uniquePhrases } from "@/lib/spans";

export function ExplanationCard({ t }: { t: Tactic }) {
  const phrases = uniquePhrases(t);
  return (
    <article className={`xcard c-${t.id}`}>
      <h4><span className="dot" />{t.name}</h4>
      <dl>
        <div>
          <dt>What it&rsquo;s doing</dt>
          <dd>{t.what}</dd>
        </div>
        {phrases.length > 0 && (
          <div>
            <dt>Found in your message</dt>
            <dd className="found">
              {phrases.map((p) => <span key={p}><mark className={`hl hl-${t.id}`} style={{ color: "inherit" }}>&ldquo;{p}&rdquo;</mark></span>)}
            </dd>
          </div>
        )}
        <div>
          <dt>What to do</dt>
          <dd className="todo">{t.advice}</dd>
        </div>
      </dl>
    </article>
  );
}
