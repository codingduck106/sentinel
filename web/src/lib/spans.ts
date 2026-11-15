import type { Tactic, TacticId } from "./api";

export interface Segment { text: string; tactic: TacticId | null }

// When evidence from two tactics overlaps, the more alarming one wins the colour.
const PRIORITY: TacticId[] = ["fear", "urgency", "reward", "authority_impersonation"];

/**
 * Turn possibly-overlapping evidence spans (from detected tactics only) into a flat list
 * of non-overlapping segments covering the whole text, so each character is painted once.
 */
export function toSegments(text: string, tactics: Tactic[]): Segment[] {
  const owner: (TacticId | null)[] = new Array(text.length).fill(null);
  const rank = (t: TacticId | null) => (t === null ? Infinity : PRIORITY.indexOf(t));
  for (const t of tactics) {
    if (!t.detected) continue;
    for (const e of t.evidence) {
      const start = Math.max(0, e.start);
      const end = Math.min(text.length, e.end);
      for (let i = start; i < end; i++) {
        if (rank(t.id) < rank(owner[i])) owner[i] = t.id;
      }
    }
  }
  const segments: Segment[] = [];
  let i = 0;
  while (i < text.length) {
    let j = i + 1;
    while (j < text.length && owner[j] === owner[i]) j++;
    segments.push({ text: text.slice(i, j), tactic: owner[i] });
    i = j;
  }
  return segments;
}

/** Unique evidence phrases for a tactic, longest first, with substrings of longer ones dropped. */
export function uniquePhrases(t: Tactic): string[] {
  const all = [...new Set(t.evidence.map((e) => e.text.trim()).filter(Boolean))].sort((a, b) => b.length - a.length);
  return all.filter((p, i) => !all.slice(0, i).some((longer) => longer.toLowerCase().includes(p.toLowerCase())));
}
