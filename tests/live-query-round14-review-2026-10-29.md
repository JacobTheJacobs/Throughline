# Throughline: live review round 14 — 29 October 2026

## Verdict and scope

Ten fresh seeded real-provider browser searches, a country-qualified geography control, live save/unsave/map-isolation checks, a live rejection/reload/agent check, UI/security fixtures, local filesystem-budget contention, and read-only inspection of the dedicated EC2. No app fixes or deployment performed. Existing untracked `demo/` and maintenance script were left alone.

**Not all fixed: selecting Edinburgh in Scotland still returns Indiana businesses and labels their location verified.** This is a content failure despite successful UI flows. The other sampled content was plausible on inspection; no population accuracy percentage is claimed, and every source claim was not independently fact-checked.

## Findings

### High: selected destination identity is lost during geographic resolution

The initial unqualified Edinburgh case offered multiple meanings; the harness selected Indiana. That is not by itself a product failure. An additional control explicitly required a Scotland/United Kingdom description and selected:

- Qloo ID `A75E2277-6EDF-4E18-831C-096E806E51AE`
- Displayed meaning: `Edinburgh`, `Geographic area · Scotland`

The returned places were Edinburgh Diner, Dollar General, Jay C, Casey's and Big Red's Place—the same Indiana results as the other selection. The Dollar General source URL is `https://www.dollargeneral.com/store-directory/in/edinburgh/1139`; the Jay C and Casey's links also contain Indiana/Edinburgh paths. The app labels them `Located in` with source `Qloo verified geographic boundary` under the Scottish selection.

`app/api/discover/route.ts:307` uses a bound entity ID only when the raw type includes `locality`; otherwise it sends `filter.location.query=seed.name`. This falls back to the ambiguous bare name. `:309–311` extracts results and labels them verified without checking the locality Qloo actually resolved. The URL response cache also shares this bare-name query across meanings; caching the URL is not the original identity error.

Fix direction: preserve/resolve the selected record to the correct supported locality, compare the resolved locality with the selected country's/region's identity, and refuse or clarify a mismatch. Do not merely change the display label or special-case Edinburgh. Qloo documents that the query form is fuzzy-matched and exposes the matched locality; it is not an identity guarantee. [Primary Qloo parameter documentation](https://github.com/qloo/docs-public/blob/main/reference/insights-api-deep-dive.md).

### Medium: explanation truncation produces broken sentences

Live Station Eleven recommendations included reasons ending `punctuated by moments of.` and `bursts of.`. `firstClause` at `app/api/discover/route.ts:196` cuts a profile at an arbitrary word and `profileReason` appends a full stop. This presents unfinished text as a finished explanation. Use a complete short sentence or an honest ellipsis. Keep profile description separate from an explanation of the specific relationship; describing a candidate's mood alone does not explain the shared subject JEV found.

### Medium: same-creator provenance loses the actual role

The live Station Eleven result includes The Penguin, labeled `Also by Helen Shaver`. The source path at `app/api/discover/route.ts:187–201` combines author, director, developer and creator properties under `creator`, and the output collapses these into `Also by`. This review does not dispute the recorded shared credit. The UX should expose the specific role and avoid implying that a credited episodic director is the creator of both series. This is an explanation/provenance precision issue, not a proven false credit.

### Medium: artwork and identity coverage remain uneven

- Diana Wynne Jones: two movie covers loaded, three book cards without image elements.
- Subnautica: three returned games, none with an image element.
- Indiana Edinburgh: two images still pending at the 10-second sample, not failed. The subsequent country-qualified control loaded all five of those images, showing that these particular images were not permanently missing.
- Nick Cave & The Bad Seeds had no linked identity for the direct-credit flow; explicit audience fallback worked. Carhartt also required the explicit fallback because no verified work was available. Keep these honest recoveries, but avoid presenting them as the initial direct flow succeeding.

### Remaining UI limitations

- Long social actions remain seed-only rather than full-map sharing; the live product has a start-only label/warning. Copy exact link preserves the map. This is now a disclosed limitation, not the earlier silent fallback.
- At 320px, the long home placeholder is clipped and Surprise is icon-only; shorter search copy would improve clarity. The screenshot was visually inspected. Controls remain reachable with no tested horizontal overflow.
- A browser-flow pass is not a semantic pass: the geography fixture passed flow checks while returning the wrong country. Add country/identity assertions to the regression oracle.

## Ten new random queries

Seed `2026102914`; stratified selection, concurrency two, real provider responses. The runner uses fresh browser contexts; saving affects only isolated test state.

| Query | Flow | Cards | Loaded art | Visible edges |
| --- | --- | ---: | ---: | ---: |
| Mitski | Direct | 5 | 5 | 5 |
| Nick Cave & The Bad Seeds | Explicit audience fallback | 5 | 5 | 5 |
| Pedro Almodóvar | Direct | 5 | 5 | 5 |
| Diana Wynne Jones | Direct | 5 | 2 | 5 |
| Carhartt | Explicit audience fallback | 5 | 5 | 5 |
| Portrait of a Lady on Fire | Direct | 5 | 5 | 5 |
| The Master and Margarita | Direct | 2 | 2 | 2 |
| Subnautica | Direct | 3 | 0 | 3 |
| Station Eleven | Direct | 5 | 5 | 5 |
| Edinburgh, Indiana selection | Direct for selected meaning | 5 | 3 | 5 |
| **Total** | **8 direct, 2 explicit fallbacks** | **45** | **37** | **45** |

Six cards had no image element; two images were pending; zero failed image elements. Fewer than five cards is not itself an error. An adaptation sharing its title with a book is not automatically a duplicate work. Additional Scottish control is excluded from these totals and is a semantic failure.

## Saving, exploring and browser-local retrieval

- The Lighthouse and Dark: save → unsave → save passed; reload retained one save per map; saving did not grow the map; Gallery hid the Qloo exploration action.
- Returning to The Lighthouse sent one map-local saved signal. Retrieved positive anchors did not include another map's liked items.
- One live agent run grew the map 5→10, streamed five additions and reported five.
- Rejection control: Nosferatu was removed, stayed absent after reload, was present in agent `dislikes` and `excludeIds`, absent from positive memory, and did not return after exploration. Map grew 4→9 after that rejection.
- First rejection-harness attempt read localStorage before debounced autosave and failed in the harness, not the app. A protocol-polled storage readiness wait fixed it; the corrected run passed.
- These are bounded sequences, not proof of all simultaneous-tab event ordering or all alias/release-edition cases. No fresh statistical JEV precision/recall benchmark was run.

## Security, server and dependency evidence

- Fourteen bounded public-route probes passed: sensitive-looking file paths 404, unsupported API GETs 405, null JSON bodies 400, foreign Origin 403, oversized JSON 400.
- Shared-map HTML/event-handler text did not execute; javascript links and an HTTP metadata-address image were dropped. These checks are not comprehensive XSS/SSRF penetration testing.
- Exact current runtime provider-key scan: two configured values, **39 files scanned**, zero skipped, **zero matching public files** across `/app/public` and `/app/dist/client`. Values never printed. Does not establish key rotation or cover non-public logs/history/other services.
- `npm audit` could not provide metadata in the standalone image. The fallback enumerated the installed dependency tree and queried npm's bulk advisory endpoint: **137 installed package names, zero returned advisories**. This is current known-advisory coverage, not a guarantee of no vulnerabilities.
- Runtime image `2026-10-29-b2eb9de`, health healthy; user node, rootfs read-only, all capabilities dropped, no-new-privileges, no app port published. Secret-file mode 600/root. Caddy log rotation configured 10 MB ×3. Disk 67% used, 2.7 GiB free. Other EC2s untouched.
- Offline budget contention: 12 independent workers ×50 calls against a real temporary ledger with cap400. **400 allowed, 200 capped, zero busy responses, final count400.** No provider calls. This closes the previously demonstrated ordinary lost-update interleaving for this test, not every stale-lock/crash scenario.
- Local lint and all **45 individual unit tests** passed. Review scripts pass syntax checks and `git diff --check`.
- Live UI fixture passed modal initial focus/Tab containment, nested confirmation containment, description preservation, Wikidata badge, gallery focus restoration and 44×44px Recents close target. Home sizes 320×568, 390×844, 768×1024, 1440×900 and 844×390 passed reachability/overflow checks; map widths320/390/768/1440 passed overflow.

No new public key exposure found within this scope. Key rotation remains unverified. Do not summarize this as “nothing leaks” or “all results accurate.”

## Reproducers and retained evidence

- `tests/live_queries_round14.py`; full query evidence `/tmp/throughline-round14-results.json`.
- Qualified geography evidence `/tmp/throughline-round14-edinburgh-control.json`.
- `tests/live_rejection_round14.py`; `/tmp/throughline-round14-rejection.json`.
- `tests/budget_parallel_round14.mjs`; `tests/runtime_asset_review_round14.mjs`.
- Existing state/UI/security/sanitization runners were rerun and their round10/round11 `/tmp` evidence refreshed.
- Sanitized SSM inspect command `22e0bd84-5c0f-40ac-af27-ecf2be8cfca8`; final runtime scan/advisory command `1f89b6e7-a7ab-4086-a2b2-281441f56f5a`.
