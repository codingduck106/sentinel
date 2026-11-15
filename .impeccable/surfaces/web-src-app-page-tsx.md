---
version: 1
slug: "web-src-app-page-tsx"
primary_target: "web/src/app/page.tsx"
related_targets: []
---

# Surface: homepage (/)

Mode: Persuade. Audience: members of the public who just got a suspicious SMS, often anxious, often on a phone. Job: understand in one glance that Sentinel is a scam text checker, and check a message without leaving the page. Proof: the real analyzer output (flagged phrases + verdict) shown working. Constraints: PRODUCT.md voice (calm, never cute, never "safe"); WCAG 2.2 AA; no stored messages.

Chosen direction: Phosphor Terminal, with the user's steer "dark, hacker black and neon green, a sense of danger but totally calm". Memorable moment: pasting a text and watching the session print each flagged phrase, then the verdict line.

## Direction contract

THESIS: The homepage is a live terminal session that checks scam texts: you paste at the prompt, Sentinel prints what it found and a verdict. It refuses the category default of a light hero with a headline, a paste box and three step icons.

OWN-WORLD: Terminal black ground, phosphor-green type and rules, a faint scanline texture, monospace (JetBrains Mono) for the headline, prompt, labels and output lines; a calm humanist sans (Atkinson Hyperlegible) for any sentence a person must read; flag lines in ink with the tactic's coloured dot as the key (text never wears a series colour); red reserved for the verdict only (Fear is burnt orange); no glow except the live cursor and the verdict line.

STORY: The visitor reads "Scam text checker." first, understands it checks texts for scams, pastes their message at the prompt, presses Check, and sees flagged phrases and a plain-language verdict with what to do next.

FIRST VIEWPORT: Top bar "sentinel_" wordmark left, two text links right. Huge monospace headline "Scam text checker." left-aligned at roughly 88px desktop. One-sentence plain subline. Below, one full-width terminal window: "$ sentinel check" prompt line, the working paste field with blinking cursor and the primary "Check" action inside the window, then example output (three flagged lines and a red verdict line) that is replaced by the real result after checking.

FORM: Phosphor Terminal, position 1 on the re-roll-2 grounded list (IMPECCABLE'S PICK). seed:d5852c7a430aef0f
Signature interaction: on Check, output lines print in sequence (about 90ms per line) like a session, ending on the verdict; reduced motion shows them at once. Motion grammar: line-by-line print and a blinking cursor only.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Unresolved
- Region-neutral advice copy (7726, £) still open from PRODUCT.md.
