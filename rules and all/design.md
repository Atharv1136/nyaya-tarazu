# Nyaya Tarazu — Design System

## Design brief, restated

Subject: an AI legal research and drafting tool for Indian criminal lawyers, whose entire mechanic is *weighing two sides against each other*. Audience: practicing advocates and public prosecutors — people who work in serious, high-stakes, text-dense environments all day, not consumers browsing a marketing site. The page's single job: make the product feel authoritative, trustworthy, and unmistakably Indian-legal in origin, while being visually distinctive enough that no one mistakes it for a generic AI SaaS tool.

Explicitly rejected directions (see `dos-and-donts.md` for the full list): purple anywhere, warm-cream-plus-terracotta-serif (the most common AI-generated look right now), near-black-plus-neon-green, glassmorphism, and any stock "AI/robot" imagery.

## Color

Dark-mode-first. Named tokens:

| Token | Hex | Use |
|---|---|---|
| `ink` | `#14161F` | Primary background — a near-black, blue-leaning charcoal, like a courtroom after hours |
| `saffron` | `#C1440E` | Primary accent — bhagva/saffron, used for CTAs, active states, the prosecution side of any split view |
| `brass` | `#D4A24C` | Secondary accent — muted antique gold, used for the 3D scale material, dividers, and the defense side of any split view |
| `indigo-robe` | `#1B2A4A` | Structural color — card surfaces, headers, the "judge's bench" tone |
| `parchment` | `#E8E1D3` | Primary text on dark backgrounds, and the surface color for any light-mode card (e.g. exported document previews) |
| `oxblood` | `#7A2E2E` | Errors/warnings only — deliberately not a typical bright red |

No green anywhere, including for success states — use `brass` for positive confirmation instead of the usual green checkmark convention.

Why this palette: saffron-and-indigo is already this founder's established brand identity (carried over from the PRD cover page and prior GitHub README work), so it's not an arbitrary choice — it's continuity. Dark ink instead of a light background avoids the cream-plus-terracotta cliché entirely while still giving the saffron accent room to feel warm and premium rather than garish.

## Type

| Role | Typeface | Notes |
|---|---|---|
| Display (headlines) | **Fraunces** | A serif with dramatic optical sizing — gives the gravitas of a printed statute or gazette notice without defaulting to the generic "AI serif" look. Use at large sizes, tight tracking, high weight contrast. |
| Body | **Public Sans** | Clean, neutral, highly legible at small sizes for dense legal text. Deliberately not Inter. |
| Data / citations | **IBM Plex Mono** | Used specifically for section numbers and citations (e.g. `BNS §103`, `IPC §302`) so a citation is instantly visually distinguishable from prose — this is a functional choice, not decoration, since citation-spotting is a real user need. |

Set a clear type scale (e.g. 14 / 16 / 20 / 28 / 44 / 64px) and use weight + size changes deliberately rather than defaulting to one weight everywhere.

## Layout concept

```
┌─────────────────────────────────────────────┐
│  [nav: logo mark]      [Product] [Docs] [Login] │
├─────────────────────────────────────────────┤
│                                               │
│      HERO — full-bleed dark ink background   │
│      Left: headline (Fraunces, large) +      │
│            one-line subhead + CTA            │
│      Right: the 3D animated scale (signature │
│            element — see below)              │
│                                               │
├─────────────────────────────────────────────┤
│   SPLIT SECTION — literal two-column layout   │
│   [ Prosecution side, saffron accent ] |     │
│   [ Defense side, brass accent ]             │
│   (used for the "how it works" explanation,   │
│    mirroring the actual product output)       │
├─────────────────────────────────────────────┤
│   Feature rows — NOT numbered 01/02/03        │
│   unless describing the real, ordered         │
│   pipeline (intake → extraction → retrieval   │
│   → dual brief → export), in which case       │
│   numbering is earned because it's a real     │
│   sequence                                    │
├─────────────────────────────────────────────┤
│   Footer — indigo-robe surface, parchment text│
└─────────────────────────────────────────────┘
```

## Signature element (the one thing to spend the "boldness budget" on)

A **3D animated scale of justice**, rendered with React Three Fiber / Three.js, sitting in the hero on a dark ink background with dramatic single-source lighting (like a courtroom spotlight). It should:

- Idle-animate with a slow, subtle sway (never perfectly still, never frantic)
- **Physically tip** based on real interaction — e.g. as the visitor scrolls into the "how it works" section, the scale visibly tilts toward whichever side (prosecution/defense) is being described, then re-balances
- Be built in `brass` and `saffron` materials with a matte-metal shader, not glossy/plastic
- Have a static, reduced-motion-safe fallback image (a still render of the same scale) for `prefers-reduced-motion` and low-power devices

This is the only heavy motion in the whole design. Everywhere else, motion should be restrained: simple fades/slides on scroll-reveal, ordinary hover states on buttons and cards — nothing competing with the hero for attention.

## Component notes

- Cards use `indigo-robe` surfaces with a 1px `brass`-at-10%-opacity border, not glassmorphism/blur effects.
- The dual-brief results view should look like two physical documents side by side (subtle paper-like texture, serif body text for the actual brief content, sans-serif for UI chrome around it) — reinforce that the output is a drafting artifact, not a chat log.
- Buttons: solid `saffron` for primary actions, outlined `brass` for secondary, never a gradient.
- Citations anywhere in the UI (e.g. "BNS §103") are always set in `IBM Plex Mono`, and are clickable/hoverable to preview the source section — this is a functional pattern carried from the PRD's citation-verification requirement, not just visual polish.

## Writing tone in the UI

- Plain, active voice, addressed to a working lawyer: "Generate both briefs," not "Unlock AI-powered legal insights."
- Empty states are invitations to act ("No case loaded yet — paste the facts to begin"), never apologetic or cutesy.
- Errors state what happened and what to do, in the interface's voice: "Couldn't verify 2 citations — review before export," not "Oops! Something went wrong."
- Every AI-generated brief carries the same persistent, plainly worded disclaimer discussed in the PRD — this is a legal-safety requirement, not just a design detail, so don't let a redesign accidentally drop it.
