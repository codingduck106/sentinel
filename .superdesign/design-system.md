# Veritas — design system

## Product context
Veritas checks a text message (SMS) someone received and tells them, in plain language, whether it looks like a scam, and *why*: which manipulation tactics it uses, shown on the exact words.
- **Audience:** the everyday public, often non-technical, often a little anxious, sometimes older, on a phone.
- **Job to be done:** "I got a weird text. Is it a scam? What should I do?" Answer in under 10 seconds, calmly, without jargon.
- **Tone:** a level-headed friend who knows about scams. Never alarmist, never cute. Plain verbs, sentence case.

### Key pages / flow
1. **Landing (`/`)**
   - Hero: headline "Got a text that feels off?" and a sample scam SMS bubble with highlighter marks drawn over the manipulative phrases, plus margin notes naming each tactic.
   - Primary CTA "Check a message".
   - A section explaining the four tactics, each shown as its highlighter swatch with a real example phrase.
   - A short, honest "What Veritas can and can't tell you" section.
2. **Message analysis (`/check`)**
   - A large message input styled like an SMS composer bubble.
   - "Paste the text you received" helper.
   - Three example chips: "Bank alert", "Prize win", "Friend's message".
   - Primary button "Check this message". Privacy line: "We don't store your messages."
3. **Results (same page, below the input, after checking)**
   - **Verdict header:** one plain sentence ("This looks like a scam", "This could be a scam", "This looks like a normal message") with a risk-level word (High / Medium / Low).
   - **Risk assessment visualization:** a horizontal risk scale (low → high) with a marker for the overall level. Beneath it, two clearly separate signals:
     - (a) "Spam pattern match", the model probability as a % with a thin bar;
     - (b) "Pressure tactics found", the four tactics as four short strength bars in their highlighter colours (0–1).
   - **The annotated message:** the user's text shown in a received-SMS bubble, with each evidence span highlighted in its tactic's colour (highlighter-pen look, slightly irregular edge).
   - **Explanation cards:** one per detected tactic. Each has the tactic name and colour chip, "What it's doing" (one sentence), "Found in your message" (quoted spans), and "What to do" (one concrete action, e.g. "Don't call the number in the text. Call your bank using the number on your card.").
   - **Next steps block** and a quiet "How this was decided" disclosure: the model trained on 2011 UK SMS; tactic detection is rule-based; it can be wrong.

## Color tokens
| token | hex | use |
|---|---|---|
| `--paper` | `#EEF1F4` | page background (cool mist; NOT cream) |
| `--surface` | `#FFFFFF` | input bubble, cards |
| `--ink` | `#1B2433` | primary text, primary button fill |
| `--ink-soft` | `#5A6577` | secondary text |
| `--line` | `#D5DBE3` | borders and dividers |
| `--hl-urgency` | `#F2B544` | amber highlighter: urgency |
| `--hl-fear` | `#E8606F` | coral highlighter: fear |
| `--hl-authority` | `#7C8CF0` | periwinkle highlighter: authority impersonation |
| `--hl-reward` | `#4FC79A` | mint highlighter: reward |
| `--risk-low` | `#2F8F6B` | |
| `--risk-med` | `#C98A12` | |
| `--risk-high` | `#C23B4E` | |

- Highlighters are used at about 45% opacity behind ink text, so text stays readable at AA.
- **Data marks (bars, dots, stripes, leader lines) do not use the highlighter hexes.** Those are too light to be marks. Marks use the mark tokens below: the same hues, with lightness snapped per mode.
  - Validated with the dataviz `validate_palette.js --pairs all`: in band, chroma floor, CVD ΔE ≥ 8, normal-vision ΔE ≥ 15, ≥ 3:1 on the surface.
  - **Light** (surface `#FFFFFF`): urgency `#C28908`, fear `#C33E51`, authority `#7B8BEF`, reward `#25A77C`. Worst CVD ΔE 8.6.
  - **Dark** (surface `#1D2532`): urgency `#C28908`, fear `#CA4557`, authority `#7B8BEF`, reward `#2FAD82`. Worst CVD ΔE 8.5.
- **Status (risk level)** is reserved meaning, kept ≥ ΔE 15 from every tactic mark and ≥ 4.5:1 on the surface, and always shipped as icon + label.
  - **Light:** low `#057743`, medium `#896105`, high `#8E021D`.
  - **Dark:** low `#2DE388`, medium `#FCB60D`, high `#FF7777`.
  - These replace the earlier `--risk-*` values, which collided with the fear and urgency marks.
- There is no other accent colour, and no gradients.
- Dark mode: paper `#141A24`, surface `#1D2532`, ink `#E8ECF2`, with highlighters at about 35% opacity.

## Typography
- **Display:** "Bricolage Grotesque", weights 600–800, slightly tight tracking (-0.02em) on large sizes.
  - Hero is 56–72px desktop and 40px mobile; H2 is 32px; H3 is 22px.
- **Body:** "Atkinson Hyperlegible", 400 and 700. 18px base on desktop, 17px mobile, line-height 1.55, max 68ch.
- **Message text** inside SMS bubbles uses Atkinson Hyperlegible at 19px.
- Do NOT use all-caps labels, eyebrows above headings, monospace data labels, or middle-dot meta strings.

## Shape, space, elevation
- **SMS bubbles:** radius 22px, with a small tail on the bottom-left for received messages (iMessage-like but neutral grey `#E4E8EE` in light mode).
- **Cards:** radius 14px, 1px `--line` border, no drop shadows (or at most one very soft shadow on the result panel). Corner radii differ by role: bubbles 22, cards 14, buttons 999 (pill), chips 999.
- Spacing scale 4 / 8 / 12 / 16 / 24 / 32 / 48 / 72 / 112.
- **Layout:** left-aligned single column, max width 1120px; the reading column is max 680px. The landing hero is two columns on desktop (headline left, annotated message right) and stacks on mobile.

## Signature element: the highlighter
- Evidence spans in a message get a highlighter mark: the background is a tactic colour with slightly rough, skewed ends (e.g. `border-radius: 0.3em 0.6em 0.4em 0.5em`, small rotation), like a real highlighter stroke.
- Each mark can carry a small margin note (desktop, to the right of the bubble) or an inline label under the bubble (mobile).
- **The one motion:** on landing-page load, the hero message's highlighter strokes draw left-to-right one after another (about 300ms each), then the margin notes fade in.
- Respect `prefers-reduced-motion` (show the final state).
- Nothing else animates on its own. Result panels may expand with a short height transition when the user checks a message.

## Copy rules
- **Button labels:** "Check a message", "Check this message", "Check another message".
- **Verdicts:** "This looks like a scam" / "This could be a scam" / "This looks like a normal message".
- **Never** say "100% safe". Always close with "If in doubt, contact the company using a number you already trust."
