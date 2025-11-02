# Nepal Armed Police Force — UI Style Guide

This style guide documents the visual system used by the ALPR & Smart Monitoring Dashboard, designed for clarity, cultural alignment with Nepal, and accessibility.

## Color Palette

- Primary (flag red): `#b91c1c` — brand highlights, hero titles, primary CTA
- Accent (navy): `#1e3a8a` — secondary CTA, focus outlines, hover states
- Surface: `#f7fafc` — panel/card backgrounds
- Foreground: `#171717` — body text on light backgrounds
- Muted: `#d1d5db` — borders, dividers, subdued text
- Success: `#15803d` — positive states, dispatched status
- Warning: `#d97706` — suspicious indicators
- Danger: `#b91c1c` — stolen indicators, critical alerts

Dark theme variants are derived automatically in CSS using `prefers-color-scheme: dark`.

## Typography

- English: Geist Sans (via `next/font/google`)
- Nepali (Devanagari): Noto Sans Devanagari (via `next/font/google`)
- Font stack: `var(--font-geist-sans), var(--font-noto-dev), ui-sans-serif, system-ui`
- Base size: 16px; headings use 1.25×–1.875× scale with tight leading

## Spacing & Layout

- Container: `container mx-auto px-4`
- Panel padding: `p-3` (desktop), `p-2` (mobile)
- Grid: `grid grid-cols-1 lg:grid-cols-2 gap-4` for dashboard panels

## Components

- Buttons: rounded `px-3 py-2`; primary uses `var(--primary)` background; secondary uses `var(--accent)`; focus-visible outline with accent
- Cards/Panels: `rounded-xl border border-muted bg-surface` with subtle elevation from color contrast, not shadows
- Tables: padded cells `p-2`, clear separators `border-t`, hover rows optional
- Badges/Status: color-code using success/warning/danger palette

## Accessibility

- High contrast color pairs; focus-visible outlines enabled globally
- Skip link at top of page (`#content`), keyboard navigation preserved
- `aria-live` on dynamic sections (tables, counts) and errors (`assertive`)
- Respect reduced motion: animations disabled under `prefers-reduced-motion: reduce`

## Motion & Micro-interactions

- Entry animations: `animate-fade-in` and `animate-slide-up`, <= 420ms
- Count-up numbers on stats; disabled under reduced motion
- Hover opacity for links and text buttons; avoid large parallax effects

## Security-conscious UI Patterns

- Confirmation prompts for dispatch/ack actions
- `rel="noopener noreferrer"` for external links (Admin)
- Avoid exposing sensitive identifiers; blur or restrict if needed (future option)

## Performance Guidelines

- Dynamic imports for heavy client-only libraries (Leaflet)
- Avoid large images and third-party script bloat
- Use polling rates that balance freshness and load; allow users to set poll intervals

## Notes

- Colors and fonts are defined as CSS variables in `globals.css` to allow easy tweaking and theming updates.
