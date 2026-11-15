import type { Tactic, TacticId } from "@/lib/api";
import { toSegments } from "@/lib/spans";

/** The user's message as a received SMS, with each evidence span highlighted in its tactic colour. */
export function AnnotatedMessage({ text, tactics }: { text: string; tactics: Tactic[] }) {
  const segments = toSegments(text, tactics);
  const present = [...new Set(segments.map((s) => s.tactic).filter(Boolean))] as TacticId[];
  // Display names come from the API (single source: TACTIC_INFO in explain.py).
  const name = Object.fromEntries(tactics.map((t) => [t.id, t.name])) as Record<TacticId, string>;
  return (
    <figure style={{ margin: 0 }}>
      <div className="bubble" aria-label="Your message, with worrying phrases highlighted">
        {segments.map((s, i) =>
          s.tactic ? (
            <mark key={i} className={`hl hl-${s.tactic}`} style={{ color: "inherit" }}>
              <span className="visually-hidden">[{name[s.tactic]}: </span>
              {s.text}
              <span className="visually-hidden">]</span>
            </mark>
          ) : (
            <span key={i}>{s.text}</span>
          ),
        )}
      </div>
      {present.length > 0 && (
        <figcaption className="legend">
          {present.map((t) => (
            <span key={t} className={`c-${t}`}><span className="dot" />{name[t]}</span>
          ))}
        </figcaption>
      )}
    </figure>
  );
}
