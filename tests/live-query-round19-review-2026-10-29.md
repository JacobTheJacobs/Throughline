# Round 19 — live UI/UX review

Date: 2026-10-29. Target: https://throughline.51-21-210-47.sslip.io

Review only: no application changes or deployment. Ten fresh, manually stratified queries across artists, people, brands, works, games and geography; not a statistically random sample. Real production providers; no mocked recommendation responses. Separate authored shared-map fixtures exercise layout and keyboard interactions, not recommendation accuracy.

## Live query results

| Query | Outcome | Initial cards | Loaded artwork |
|---|---|---:|---:|
| Caroline Polachek | Flow pass | 5 | 1 |
| Fleet Foxes | Flow pass | 5 | 4 |
| Kelly Reichardt | Flow pass | 5 | 5 |
| Yoko Ogawa | Flow pass | 5 | 2 |
| Moleskine | Flow pass; sparse result | 1 | 0 |
| Perfect Blue | Flow pass | 5 | 5 |
| The Memory Police | Explicit audience fallback, then flow pass | 3 | 3 |
| Citizen Sleeper | No usable map; explicit unsupported-record recovery | 0 | — |
| We Are Lady Parts | Flow pass | 3 | 3 |
| Bologna | Flow pass | 5 | 5 |

Eight primary flow passes, one user-visible fallback, one unsuccessful search. Across successful/fallback maps: 37 cards and 37 visible connections, 28 loaded covers, seven cards without image elements and two failed cover requests after the bounded artwork settle. No horizontal overflow in the recorded map snapshots. Flow checks cover opening a card, explanation, save count, unchanged graph on saving, persistence after reload and gallery access. They do not certify every provider description or recommendation as correct.

## Confirmed issues, prioritized

1. **Medium — music artwork remains unreliable.** Caroline Polachek has artwork on only one of five cards. Desire, I Want to Turn Into You and Pang had failed Cover Art Archive requests; Arcadia and Ocean of Tears had no image element. The screenshot shows designed fallback tiles rather than raw broken-image icons, but four text-heavy substitutes weaken the visual map. Fleet Foxes is missing one cover; Yoko Ogawa three; Moleskine its sole cover. Do not confuse missing artwork with missing edges: all 37 edges were visible. Gallery images also lack the map's image error/retry handling (`app/page.tsx:389`), a source-level resilience gap, not a separately induced live gallery failure.
2. **Medium — unsupported game search still dead-ends.** Citizen Sleeper returns “Qloo does not support audience matches from this videogame record” and only Change search. This is an explicit coverage limitation, not evidence that JEV crashed. It is nevertheless an unsuccessful product journey after the homepage invites game searches. Offer a supported, clearly named related starting point only when evidence exists; never silently substitute another entity.
3. **Medium — gallery touch targets are small.** Live DOM measurements: save hearts 38×38px on all tested widths; Share 40px wide on mobile; tablet gallery filters 32px high. These fall short of a comfortable 44×44px touch target (not a claim of WCAG AA failure). Card title buttons are about 34px high, although the larger image also opens details.
4. **Medium — gallery title hierarchy sacrifices identification.** At 390px the fixture's “The Memory Police” becomes “The Memory P…” and a longer title “Everything Eve…”. The card spends substantial height on artwork/fallback initials while forcing the title to one line beside the heart. Allow two title lines and reserve separate action space. Users can open details to recover the name, so this is friction rather than inaccessible content.
5. **Low — empty filters dominate gallery navigation.** The three-book fixture shows many disabled zero-result categories before Books. On a narrow horizontal filter row this pushes useful filters out of view. Keep New/Loved and populated categories immediately visible; place the rest behind a deliberate category chooser.
6. **Low — mobile homepage placeholder is clipped.** At 390px the category list is cut off by Explore. Search is reachable and functional, but shorter copy such as “Search anything you love” would be clearer. Surprise me is icon-only on mobile; it retains an accessible label but loses visible explanation.

Additional coverage observation: Moleskine produces one text-only card. This passes the current “up to five” contract, but looks weak. A sparse result needs a concise explanation and an evidence-backed next action, not filler cards.

## Checks that passed

- Home search reachable without horizontal overflow at 320×568, 390×844, 768×1024, 1440×900 and short landscape 844×390.
- Gallery no horizontal overflow at 320, 390, 768 and 1440 widths; single column at 320, two columns at 390.
- Authored fixture: newest-first order, Loved restricts to one saved item, Explore with Qloo hidden in gallery details.
- Share initial focus and Tab containment; three repeated nested confirmation keyboard cycles; focus returns to originating gallery card after closing details.
- Exact-share fixture preserves descriptions; long social sharing intentionally becomes seed-only, not a complete-map claim.
- Mobile recents close control is 44×44px.

## Evidence

- Runner: `tests/live_queries_round19.py`; results `/tmp/throughline-round19-results.json`; full run `/tmp/throughline-round19-run.log`.
- UI fixture: `tests/live_gallery_round19.py`; `/tmp/throughline-round19-gallery.json` and gallery screenshots at 320/390/768/1440.
- Actual Caroline Polachek map: `/tmp/sideways-round8-artist-0.png` (legacy screenshot filename).
- Responsive home screenshots: `/tmp/throughline-round10-home-{width}.png` (reused runner, freshly executed).
- Keyboard fixture results: `/tmp/throughline-round11-ui.json`; wait-aware confirmation runner `tests/live_confirm_round16.py`.

No server/security certification or exhaustive semantic accuracy claim is made by this UI-focused pass.
