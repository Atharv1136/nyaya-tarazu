# Nyaya Tarazu — Do's and Don'ts

Read this before writing any UI code. It exists because most AI-generated interfaces converge on the same handful of looks, and this product should not look like that.

## Don'ts — hard rules, no exceptions

- **No purple.** Not lavender, not indigo-leaning-purple, not a "violet" gradient anywhere — not in buttons, not in hover states, not in charts, not in loading spinners. If a color picker suggests purple as a "complementary" accent, reject it.
- **No purple-to-blue or purple-to-pink gradient hero sections.** This is the single most common "AI startup" background and it's banned outright.
- **No generic AI-tool look.** Concretely, that means: no warm-cream background paired with a terracotta/clay accent and a big serif headline (this is the single most common AI-generated aesthetic right now); no near-black background with a single neon acid-green or vermilion accent; no glassmorphism cards floating on a blurred gradient; no rounded-blob illustrations; no stock "AI robot / neural network / circuit board" imagery anywhere.
- **No green**, in any shade, anywhere in the interface — including for "success" states. Use warm gold/amber for positive confirmation instead.
- **No Inter as the default font.** It's the single most overused typeface in AI-generated UI and instantly reads as templated. Use the type system defined in `design.md`.
- **No numbered-step markers (01 / 02 / 03) as decoration** unless the content is a genuine sequence (e.g. the actual 30-day build order). Don't sprinkle them on feature grids just to look organized.
- **No stock "two people shaking hands" or "lawyer with gavel in an empty stock-photo office" imagery.** If a photo-style image is needed, it should look like an actual Indian courtroom/district-court context, not generic Western legal stock photography.
- **Don't make the dual-brief output look like a chat conversation.** It should read like an actual legal brief on a page — this is a drafting tool, not a chatbot.

## Do's

- Follow the palette, type system, and signature element defined in `design.md` exactly — don't substitute a "close enough" default.
- Build the 3D element as a real, deliberate, single signature moment (the animated scale of justice described in `design.md`), not scattered decorative 3D everywhere. One strong moment beats five weak ones.
- Respect `prefers-reduced-motion` — the 3D scene and any scroll animation must have a static fallback.
- Keep the two-sided (prosecution/defense) structure visually literal wherever it makes sense — a real split, not just two cards side by side with no relationship implied.
- Write every label, button, and empty state in plain, active-voice language a lawyer would actually use — not generic SaaS copy ("Unlock your potential," "Empower your workflow," etc. are banned phrases).
- Test the design at actual courtroom-use scenarios: someone reading this on a laptop between hearings, in a hurry, not someone leisurely browsing a marketing site.
- Ship dark-mode-first (see `design.md`) but make sure text contrast passes accessibility checks — this is a professional tool, not a mood board.

## Before you ship any screen, ask

1. Does this look like something only Nyaya Tarazu would produce, or could I paste this same layout into any other legal-tech pitch and it would still fit?
2. Is there purple, cream+terracotta, or neon-on-black anywhere? If yes, stop and redo it.
3. Does the one signature 3D moment feel earned, or did I add motion just because I could?
