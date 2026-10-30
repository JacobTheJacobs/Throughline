# Round 20 — ten fresh live searches and UI/UX review

2026-10-29. Production: https://throughline.51-21-210-47.sslip.io

Review only. No application code changes or deployment. Queries selected with recorded random seeds from ten new category-specific pools; this is a stratified sample, not a representative accuracy benchmark. Recommendation responses were real, not mocked.

## Live searches

| Query | Flow | Cards | Loaded artwork |
|---|---|---:|---:|
| FKA twigs | Pass | 5 | 5 |
| Massive Attack | Pass | 5 | 5 |
| Bong Joon-ho | Pass | 5 | 5 |
| Kazuo Ishiguro | Pass | 5 | 5 |
| Muji | Pass | 5 | 0 |
| Fantastic Mr. Fox | Pass | 5 | 5 |
| Piranesi | Pass | 2 | 2 |
| Hollow Knight | Pass | 3 | 1 |
| Fleabag | Pass | 3 | 3 |
| Ljubljana | Pass | 5 | 5 |

Ten primary flow passes, no fallback and no unsuccessful search. 43 cards, 43 visible edges, 36 loaded images, seven absent-image fallbacks, zero failed or pending images in bounded visual snapshots. All completed card opening, saving without graph expansion, saved-count persistence after reload, and gallery access. No recorded page errors. These checks do not independently verify every description, credit, or recommendation's semantic relevance.

## New confirmed UI issue

**Medium: gallery and saved brief lack failed-image fallback.** A separate authored shared-map fixture intentionally aborted image requests in the browser only. Both gallery and brief retained an image with naturalWidth=0, without inserting their fallback. The gallery visibly displayed a browser broken-image symbol and empty rectangle. This reproduces the source-level gap noted in round 19; it does not mean production providers failed in the ten-query sample. Map retries do not protect the independently rendered gallery/brief images. Use one reusable artwork component with loading, successful, unavailable and failed states across all surfaces.

Evidence: `tests/live_art_failure_round20.py`, `/tmp/throughline-round20-art-failure.json`, `/tmp/throughline-round20-art-failure.png`. Source: `app/page.tsx` gallery renderer and brief renderer.

## Remaining UI findings

- **Medium: visual quality depends heavily on entity type.** Muji returned five cards, none with artwork. Hollow Knight had covers on only one of three. Unlike a failed URL, these are missing-artwork cases. Make intentional category-specific placeholders attractive; do not substitute unrelated images. The previous Caroline Polachek cover failures were not retested by these new queries.
- **Medium: gallery selection is conveyed visually, not programmatically.** `app/page.tsx:389` applies an active CSS class to filter buttons but no aria-pressed/aria-current. A screen-reader user cannot obtain the same selected-filter state from the button semantics. Give filter buttons a consistent selected-state attribute and announce the updated result count. This is source inspection, not a full assistive-technology audit.
- **Medium: mobile titles and touch targets remain as measured in round 19.** Gallery hearts were 38×38px; title labels truncate to one line even when a two-line treatment would identify items better. No application changes occurred between reviews. These measurements were not re-collected in round 20.
- **Low: zero-result category clutter and clipped homepage placeholder remain.** Prefer populated categories up front, and shorter mobile search copy. Keep accessible labels for icon-only actions.
- **Product tradeoff, not a failure:** Piranesi returned two cards; Hollow Knight and Fleabag three. This satisfies up-to-five, but explain sparse results briefly instead of suggesting a fixed five were added or padding with weak matches.

## Repeated checks that passed

- Home input reachable and no horizontal overflow at 320×568, 390×844, 768×1024, 1440×900 and 844×390.
- Share focus starts inside dialog and Tab wraps inside.
- Three nested confirmation keyboard cycles retain focus and restore it on close.
- Inspector focus returns to gallery on close.
- Exact-share fixture preserves reference descriptions; long social sharing intentionally uses a seed-only link.

The fixtures use explicitly authored maps and browser-local clipboard/window.open interception, not fake provider success. No public shares were posted.

## Evidence files

- `tests/live_queries_round20.py`
- `/tmp/throughline-round20-results.json`
- `/tmp/throughline-round20-run.log`
- `/tmp/throughline-round11-ui.json` (reused runner, freshly executed)
- `/tmp/throughline-round10-shared-safety.json` and home screenshots (reused runner, freshly executed)
- `/tmp/sideways-round8-artist-0.png` and `artist-1.png` (legacy filenames, freshly captured actual artist maps)

Scope: UI/UX and flow review, not a new server/security audit or exhaustive factual certification.
