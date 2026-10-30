# Throughline live review — round 13, 2026-10-29

## Scope and verdict

Ten fresh stratified random queries, seed `2026102913`, against production using real provider-backed browser flows, concurrency two. Separate shared-map fixtures test UI and injection defenses without pretending to test recommendation accuracy. Read-only inspection targets only the dedicated Throughline EC2. No deployment or application implementation changes were made in this pass.

**Browser-flow success does not mean content correctness. A serious false classification and unsupported adaptation wording were found. Do not call the results universally verified.**

## Findings, ordered by impact

1. **High — a policy plan becomes a movie adapted from Orwell.** The real George Orwell search returned `wikidata:Q122382481`, Project 2025, as `movie`, with reason “Project 2025 is adapted from a work by George Orwell.” Its own returned description says it is a Heritage Foundation policy plan. Local reproduction confirms `wikidataWorkType([], description)` returns undefined, then `directConnectionType('Based on a work by','author',undefined)` invents `movie`; `directConnectionReason` supplies the stronger adaptation claim. See `lib/direct-connections.ts:7,20` and `app/api/discover/route.ts:125–135`. The generic Wikidata P144 path is insufficient to establish a film adaptation, and the fallback is not constrained to a positively identified supported work class. This is not evidence that JEV generated the claim: it is the direct-relationship path. The current upstream cause of the returned P144 association was not independently established; stale or incorrect source data must not become a stronger verified product claim. [Entity record](https://www.wikidata.org/wiki/Q122382481), [P144 semantics](https://www.wikidata.org/wiki/Property:P144).
2. **High — budget updates still have a lost-update race.** Local code changed during the review and now fails closed on storage errors; that earlier issue must not be reported as still unfixed locally. However, `readLedger → increment → writeLedger` is not a transaction. `node --experimental-strip-types --no-warnings tests/budget_concurrency_review.mjs` forces two independent module/worker callers to read count 399 before either writes. Both are allowed under cap 400; final count is only 400. No provider calls occur. Atomic file replacement prevents partial JSON, not concurrent reservation loss. Overlapping containers/processes need serialization or transactional reservations. The test controls scheduling to demonstrate the possible interleaving, not its natural production frequency.
3. **Medium — production remains on the older image.** SSM reports `2026-10-29-audit10-final`, `health=null`, and empty Caddy log-rotation options. Several local UI/server fixes therefore remain unverified live. App isolation remains enabled: user=node, read-only rootfs, capabilities ALL dropped, no-new-privileges; app logs are capped at 3×10 MB. Secret file is mode 600/root. Disk is 62% used with 3.1 GiB free. Read-only command ID: `459e7540-3e79-4684-bfa6-5bfd51083809`.
4. **Medium — sharing and focus still fail live.** Fixture test: share initial focus and Tab containment false, descriptions omitted, long social links reduced to seed-only, factual brief badge says Qloo, gallery opener focus not restored. Nested removal confirmation passed on this run. Local improvements exist but do not constitute production verification. The gallery restore expression still prefers an existing hidden map button over the gallery opener.
5. **Medium — artwork coverage still has gaps.** George Orwell: 0/5 covers; Journey: 0/3; David Bowie: 4/5. These nine cases have no image element, not broken loaded images. Never substitute unrelated artwork merely to fill the space. Missing art is visible degraded coverage even when fallback rendering behaves correctly.
6. **Medium — test oracle misses semantic contradictions.** The generic live harness reports FLOW_PASS for the Orwell result because it checks flow, IDs and relation formatting, not whether a policy plan is a movie. The 44 passing unit tests do not cover this counterexample. Add positive type-evidence assertions and relation-semantic fixtures; do not optimize solely for passing flow counts.
7. **Low — remaining mobile polish.** The inspected 390px home screenshot has a visibly clipped long placeholder and an icon-only Surprise control; a shorter placeholder and clearly discoverable accessible action would improve clarity. Social buttons still use text-glyph stand-ins locally. Live Recents close target is 30×30px. No horizontal overflow was detected in the tested viewport set.

## Ten-query results

| Query | Browser flow | Cards | Loaded art | Visible edges |
| --- | --- | ---: | ---: | ---: |
| Cocteau Twins | Pass | 5 | 5 | 5 |
| David Bowie | Pass | 5 | 4 | 5 |
| David Lynch | Pass | 5 | 5 | 5 |
| George Orwell | Pass; content failure above | 5 | 0 | 5 |
| Aesop | Explicit audience fallback | 5 | 5 | 5 |
| Aftersun | Pass | 3 | 3 | 3 |
| The Name of the Rose | Pass | 5 | 5 | 5 |
| Journey | Pass | 3 | 0 | 3 |
| Twin Peaks | Pass | 3 | 3 | 3 |
| Porto, Italian-area choice | Pass for selected identity | 5 | 5 | 5 |
| **Total random sample** | **9 direct, 1 fallback** | **44** | **35** | **44** |

Zero failed image elements, nine absent-image fallbacks. This sample is not a statistical relevance benchmark.

Porto ambiguity was explicitly offered; the harness initially selected an Italian area. An additional country-qualified control selected “Area in Portugal”, Qloo ID `0432AF3B-F35C-4F8B-911C-8E2D86C654CC`, and returned Livraria Lello, Torre dos Clérigos, Vila do Conde, NorteShopping and Parque de Serralves. This confirms the qualified flow, not that the unqualified query infers Portugal. Geographic boundary labels should communicate city versus wider region clearly.

## Saving, agent and local retrieval

Live The Lighthouse and Dark each passed save → unsave → save, reload persistence, no expansion on save, and hiding Qloo exploration in Gallery. Returning to The Lighthouse sent exactly one map-local saved signal; retrieved positive anchors did not include the other map. One actual agent run grew 5→10 cards and streamed/reported exactly five additions. Map overflow passed widths 320, 390, 768, 1440. These bounded checks do not cover simultaneous-tab conflicts or independently establish the semantic quality of every agent recommendation. Incorrect direct records can still be saved and become subsequent retrieval input; provenance does not eliminate that accuracy problem.

## Security and responsive checks

- All 14 bounded public-route probes passed: six sensitive-looking file paths 404, unsupported API GETs 405, null bodies 400, foreign Origin 403, oversized discovery JSON 400.
- Authored HTML/event-handler shared text did not execute, javascript links were dropped, and an HTTP metadata-address image was dropped.
- Home input reachable with no horizontal overflow at 320×568, 390×844, 768×1024, 1440×900 and 844×390. Mobile Recents visible. 390px screenshot visually inspected.
- Latest local lint and **44 individual unit tests** passed. No production build/deployment performed in this pass.
- Public-route and asset scans are bounded checks, not proof that nothing leaks. Provider-key rotation remains unverified; no credentials were printed by these checks.
- Exact local-key scan fetched nine public assets, found zero matches for two configured values, and encountered ten fetch failures. This is incomplete coverage and must not be presented as a clean full-bundle or production-secret scan.

## Reproducers / evidence

- `tests/live_queries_round13.py`; complete provider/browser evidence `/tmp/throughline-round13-results.json`.
- `tests/budget_concurrency_review.mjs` (offline controlled interleaving).
- Existing runners: `live_security_round10.py`, `live_shared_safety_round10.py`, `live_state_round10.py`, `live_ui_review_round11.py`; their `/tmp/throughline-*` outputs were refreshed in this pass.
- `tests/public_asset_review_round13.py` scans bounded public assets for exact locally configured provider-key values without printing them; it does not establish whether production uses the same keys.
