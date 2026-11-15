---
name: Sentinel
description: A scam text checker that runs as a live terminal session; paste a message at the prompt and it prints the pressure words it found and a verdict.
colors:
  terminal-black: "#040705"
  panel-black: "#08110b"
  phosphor-white: "#d8f5e0"
  faded-phosphor: "#8db89a"
  scan-rule: "#1d3a26"
  bubble-green: "#0c1a11"
  phosphor: "#39ff6a"
  phosphor-dim: "#1f9e45"
  on-phosphor: "#031008"
  wash-urgency: "#f2b544"
  wash-fear: "#e8763a"
  wash-authority: "#7c8cf0"
  wash-reward: "#c45fd0"
  mark-urgency: "#c28908"
  mark-fear: "#bb4717"
  mark-authority: "#7b8bef"
  mark-reward: "#b838be"
  risk-low: "#4fd1c5"
  risk-medium: "#ffcc4d"
  risk-high: "#ff8f8f"
typography:
  display:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: "clamp(40px, 6vw, 74px)"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: "clamp(24px, 3.4vw, 32px)"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.03em"
  title:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: "19px"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.03em"
  body:
    fontFamily: "Atkinson Hyperlegible, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 400
    lineHeight: 1.55
  terminal:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.4
rounded:
  sm: "4px"
  md: "6px"
  lg: "8px"
  pill: "999px"
spacing:
  xs: "8px"
  sm: "16px"
  md: "24px"
  lg: "40px"
  xl: "64px"
  gutter-mobile: "16px"
  frame: "1120px"
  read: "680px"
components:
  button-primary:
    backgroundColor: "{colors.phosphor}"
    textColor: "{colors.on-phosphor}"
    typography: "{typography.terminal}"
    rounded: "{rounded.md}"
    padding: "14px 26px"
  button-primary-disabled:
    backgroundColor: "transparent"
    textColor: "{colors.faded-phosphor}"
    rounded: "{rounded.md}"
  chip:
    backgroundColor: "transparent"
    textColor: "{colors.phosphor-white}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "6px 12px"
  input-terminal:
    backgroundColor: "{colors.terminal-black}"
    textColor: "{colors.phosphor-white}"
    rounded: "{rounded.md}"
    padding: "16px 16px 36px"
  terminal-window:
    backgroundColor: "{colors.panel-black}"
    textColor: "{colors.phosphor-white}"
    rounded: "{rounded.lg}"
    padding: "16px 24px 22px"
  results-panel:
    backgroundColor: "{colors.panel-black}"
    textColor: "{colors.phosphor-white}"
    rounded: "{rounded.lg}"
    padding: "32px"
  level-tag:
    backgroundColor: "transparent"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "1px 8px"
---

# Design System: Sentinel

## Overview

**Creative North Star: "Phosphor Terminal"**

Sentinel is a live terminal session that checks scam texts. The homepage does not describe a tool; it is the tool: a `$ sentinel check` prompt with a blinking cursor, a paste field inside the window, and a transcript that prints flagged phrases line by line and ends on a verdict. The ground is terminal black with a breath of green, type and rules glow phosphor green, and a faint scanline texture belongs to the screen itself rather than sitting on top as decoration.

The binding user steer for this world is "dark-themed, the typical 'hacker' black and neon green vibe; a sense of danger, but also totally calm". The danger lives in the vocabulary (a terminal reading a hostile message, red reserved for one word of verdict); the calm lives in the restraint: soft phosphor-white reading text rather than neon, flat panels, hairline rules, a single motion moment, and a humanist sans for every sentence a frightened person has to read. This world replaced the earlier light "Veritas" system by explicit user decision, which also lifted that system's ban on a dark security-console look.

The wordmark is lowercase `sentinel_` in JetBrains Mono 800, ink with the trailing underscore in phosphor green, standing in for the cursor.

**Key Characteristics:**
- Dark only (`color-scheme: dark`); terminal black page, panel black windows.
- Phosphor green is the brand: headline, prompt glyph, cursor, primary action, focus ring.
- Monospace for machine voice (headings, prompt, output lines, labels); Atkinson Hyperlegible for human sentences.
- Text never wears a series colour; tactic colours appear only as dots, bars and highlighter washes.
- Flat surfaces, 1px hairline rules, 4 to 8px corners.
- One motion moment: the transcript prints line by line; the cursor blinks. Both stop under reduced motion.

## Colors

Near-black greens with one luminous phosphor accent, four validated tactic hues for evidence, and three reserved status hues for risk.

### Primary
- **Phosphor** (`phosphor`): the brand voice. Hero headline, page titles on the check route, the `$` prompt, the cursor block, the primary button fill, focus outlines, `::selection`, the risk-scale marker, the spam-score figure, the closing line, `+`/`-` disclosure glyphs.
- **Phosphor Dim** (`phosphor-dim`): the quieter green. The terminal window border, the `>` glyph before each output line, chip hover borders, the inline error/alert border, emphasised flow nodes.
- **On Phosphor** (`on-phosphor`): text on a phosphor fill (the Check button, selection).

### Secondary (tactic series)
Each tactic has a **mark** (dots, meter bars, tooltip keys) and a lighter **wash** (the translucent highlighter behind evidence words, mixed at about 40% so ink stays readable on top).
- **Urgency Amber** (`mark-urgency` / `wash-urgency`).
- **Fear Burnt Orange** (`mark-fear` / `wash-fear`): deliberately orange, not red, so red is reserved for the High verdict.
- **Authority Periwinkle** (`mark-authority` / `wash-authority`).
- **Reward Orchid** (`mark-reward` / `wash-reward`): orchid, not green, because green belongs to the brand.

The mark set is validated with the dataviz validator (`--mode dark --surface #08110b --pairs all`): colour-vision-deficiency separation dE 8.9, normal-vision separation dE 15.7, each at least 3:1 on the panel.

### Tertiary (status)
- **All-Clear Teal** (`risk-low`), **Caution Yellow** (`risk-medium`), **Alarm Rose** (`risk-high`). Reserved for risk level only: each is at least dE 15 from every tactic mark and at least 8:1 on the panel, and always ships with an icon and a written label. The High verdict line is the one place a reddish hue appears as type.

### Neutral
- **Terminal Black** (`terminal-black`): page ground, input wells inside the terminal, theme colour.
- **Panel Black** (`panel-black`): raised windows: the terminal, the results panel, flow nodes, tooltips.
- **Bubble Green** (`bubble-green`): the received-message bubble and the flow start node.
- **Phosphor White** (`phosphor-white`): all reading text. Calmer than neon by design.
- **Faded Phosphor** (`faded-phosphor`): secondary text, placeholders, captions, nav links (8.6:1 on panel).
- **Scan Rule** (`scan-rule`): every hairline, border and divider.

### Named Rules
**The Reserved Red Rule.** Red-family hue as type belongs to the High verdict alone. Fear is burnt orange; errors use phosphor-dim borders, not red.

**The Ink-Not-Series Rule.** Text never wears a tactic colour. A flagged line is ink, keyed by the tactic's dot; evidence words are ink on a wash.

**The Green Is The Brand Rule.** No tactic or status hue may be green; green means Sentinel itself.

## Typography

**Display Font:** JetBrains Mono (with ui-monospace, monospace), weights 400, 700, 800
**Body Font:** Atkinson Hyperlegible (with system-ui, sans-serif), weights 400, 700

**Character:** The machine speaks in mono: tight, negative-tracked, confident. The human sentences are set in a hyperlegible humanist sans so explanations and advice read calmly for anyone, including people reading under stress.

### Hierarchy
- **Display** (800, clamp 40 to 74px, 36px on phones, line-height 1, tracking -0.04em, tightened word spacing): the hero headline in phosphor.
- **Headline** (700, clamp 24 to 32px, line-height 1.1): section titles in ink. The check page title is a larger 30 to 44px phosphor variant; the verdict heading runs 28 to 36px.
- **Title** (600, 17 to 20px): tactic names, explanation card heads, flow nodes, signal heads.
- **Terminal** (400, 16px; textareas 17px, line-height 1.6): the prompt line, transcript lines, the paste field, button labels.
- **Body** (Atkinson 400, 18px desktop, 17px phones, line-height 1.55): every sentence a person must read; measure capped around 60 to 65ch (`hero-sub` 60ch, AI note 65ch, limits and method notes 62ch).
- **Label** (14 to 15px): chips, level tags, counters, legend entries, scale labels, privacy line.

### Named Rules
**The Two Voices Rule.** Mono for what the machine says (headings, prompt, output, labels); Atkinson for what a person must understand (explanations, advice, captions). Never set a paragraph of advice in mono.

## Layout

A single centred frame (1120px max, 24px side padding, 16px on phones) with a reading column of 680px on the check route. The homepage is one column: top bar, left-aligned hero, then a full-width terminal window, then results directly beneath, then sections divided by full-width hairlines with 64px vertical padding. The tactic glossary is a two-column definition grid (300px term, fluid description) that stacks below 720px; the can/can't block is two equal columns to 860px. Spacing steps cluster on 8, 16, 24, 40 and 64px. Below 640px the primary button goes full width, panels drop to 16 to 20px padding, and body text steps to 17px.

## Elevation & Depth

Flat. Depth comes from tonal steps (terminal black ground, panel black windows, bubble green for the message) and 1px hairlines, plus the faint 1-in-4px scanline gradient on the page. There is no shadow vocabulary for surfaces.

### Shadow Vocabulary
- **Cursor glow** (`box-shadow: 0 0 10px rgb(57 255 106 / .55)`): the blinking prompt cursor only.
- **Verdict glow** (`text-shadow: 0 0 14px` of the risk colour at 45%): the verdict line in the transcript only.

### Named Rules
**The Two Glows Rule.** Glow exists in exactly two places: the live cursor and the verdict line. Nothing else emits light.

**The No Nesting Rule.** A panel never sits inside another bordered panel; subdivisions inside a panel are hairline top rules (signals, explanation cards, method notes), not cards.

## Shapes

Gently squared corners: 4px for chips, level tags and the focus ring; 6px for buttons, inputs and inline alerts; 8px for windows and panels; full pill only for dots and the ends of the risk scale. Borders are 1px in scan rule, or phosphor dim when a window is the active instrument. The transcript is separated from the input by a dashed hairline, the terminal's own divider. Meters are square at the baseline and rounded 4px at the data end.

## Components

### Buttons
Lit and decisive: the primary action is the brightest object on the page after the headline.
- **Shape:** gently squared (6px).
- **Primary:** phosphor fill, on-phosphor mono 700 label, 14px by 26px padding; lit at rest, never a ghost. Hover lightens the fill. Busy state swaps the label for a spinner and "Checking…".
- **Empty press:** pressing Check with nothing pasted shows an inline alert under the field with a phosphor-dim border, not red.
- **Disabled (over length):** transparent with a 1px scan-rule ring and faded label.
- **Text link:** faded phosphor, underlined at 4px offset; used for "Check another message" and secondary moves.

### Chips
- **Style:** transparent, 1px scan-rule border, mono 14px ink, 4px corners. Used for the example messages.
- **Hover:** border goes phosphor dim, text goes phosphor.

### Cards / Containers
- **Corner Style:** 8px.
- **Background:** panel black.
- **Shadow Strategy:** none (see Elevation).
- **Border:** 1px scan rule; the terminal window uses phosphor dim.
- **Internal Padding:** 16 to 24px for the terminal, 32px for results (20px on phones).

### Inputs / Fields
- **Style:** mono 17px ink on terminal black (inside the terminal) or panel black (check route), 1px scan-rule border, 6px corners, extra bottom padding to hold the character counter.
- **Focus:** border and a 1px ring both phosphor; the caret is phosphor everywhere.
- **Error:** the counter turns alarm rose and reads "too long".

### Navigation
Top bar: the `sentinel_` wordmark left, two Atkinson text links right in faded phosphor that turn ink and underline on hover. No menu, no button in the bar.

### Terminal Window (signature)
The page's instrument. A `$ sentinel check` line with a phosphor `$` and a blinking phosphor cursor, the paste label and example chips, the field, the AI opt-in, the Check button and privacy line, then a dashed rule and the transcript. Each transcript line opens with a phosphor-dim `>`. Flag lines: tactic dot, tactic name in ink 700, the quoted evidence in faded phosphor. Info lines in faded phosphor. The verdict line sits above a hairline, in the risk colour at 22 to 26px 800 with its glow, followed by an outlined level tag. Before any check, a real example transcript shows at reduced opacity.

Motion: on a result, lines print one at a time about 110ms apart, each revealing left to right over 220ms; the cursor blinks on a 1.1s step. Under `prefers-reduced-motion` every line appears at once and the cursor holds still.

### Highlighter
Evidence words in the received message are painted with a translucent wash of their tactic, a slightly irregular rounded stroke that follows line wraps, ink text on top. A legend of dots and names sits under the message.

### Risk Display
A three-segment scale (washes of the three status hues, the active segment solid) with a phosphor marker; a written status with an icon; meters whose fill carries the colour over a tinted track; a table twin of every chart behind a disclosure.

## Do's and Don'ts

### Do:
- **Do** keep the page dark only, on terminal black (#040705), with the scanline texture at its current faintness.
- **Do** set headings, the prompt, transcript lines, labels and buttons in JetBrains Mono, and every explanatory sentence in Atkinson Hyperlegible at 17 to 18px with a measure near 60 to 65ch.
- **Do** key tactic lines with a coloured dot and leave the text in ink.
- **Do** pair every risk colour with an icon and a written level.
- **Do** keep the primary Check button lit phosphor at rest.
- **Do** divide inside a panel with 1px hairline top rules.
- **Do** honour reduced motion by showing the full transcript at once and stopping the cursor.

### Don't:
- **Don't** use a red-family hue for anything except the High verdict; fear stays burnt orange and errors use phosphor dim.
- **Don't** colour text with a tactic hue, or introduce any green that is not the brand.
- **Don't** add glow beyond the cursor and the verdict line.
- **Don't** add motion beyond the line-by-line print and the cursor blink.
- **Don't** nest bordered cards or use coloured side stripes on containers.
- **Don't** exceed 8px corner radius on surfaces, or add drop shadows to panels.
- **Don't** set long reading text in mono, or in neon phosphor.
