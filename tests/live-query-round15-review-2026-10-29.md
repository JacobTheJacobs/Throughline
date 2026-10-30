# Throughline: live review round 15 — 29 October 2026

## Verdict

The latest geographic fix works for an initial Scottish search but **still loses the selected geography during nested exploration**. A second, synthetic test of the actual production validator confirms that matching a country can incorrectly override a conflicting region. These are the primary remaining accuracy findings.

Ten additional real-provider browser flows completed, but flow success is not independent semantic verification. No application edits or deployment performed. Only review scripts/report were added; existing untracked demo and maintenance files were preserved.

## Findings

### High — geographic identity still depends on exploration depth

`tests/live_geography_round15.py` posts the same selected Scotland ID, name, type and requested category at depth1 and depth2:

```
entityId: A75E2277-6EDF-4E18-831C-096E806E51AE
name: Edinburgh
entityType: destination
types: [place]
```

- **Depth1:** Royal Botanic Garden Edinburgh, Edinburgh Castle, Camera Obscura & World of Illusions, Edinburgh Festival Fringe Society, The Dome.
- **Depth2:** Edinburgh Diner, Dollar General, Jay C, Casey's, Big Red's Place. Linked URLs explicitly include `/in/edinburgh/` and `in-edinburgh` for Indiana.

Both return HTTP200. The nested response still presents these as located in the selected Edinburgh with verified geographic-boundary provenance. The geography regression exits1, correctly detecting the content failure.

Root cause: `app/api/discover/route.ts:269` hydrates a supplied entity ID only when `requestDepth===1 && name && !externalId`. Nested requests construct a minimal seed without authoritative geographic metadata. In `:307–310`, missing lineage yields an empty `within` array, a bare-name location query, and an always-true `confirmsArea` predicate. The initial-search fix therefore does not protect subsequent card/category exploration. Hydrate the geographic identity independently of depth/external-link presence or resolve an authoritative supported locality before querying; do not trust a bare name as the identity.

### Medium — shared-country matching does not confirm a selected region

`confirmsArea` uses `within.some(...)`. In `tests/geography_predicate_round15.mjs`, the **actual production helper** is exercised with explicitly synthetic data:

- Selected: Ontario, Canada.
- Candidate: Vancouver, British Columbia, Canada.
- Actual: accepted=true; expected=false.

No provider results are fabricated by this test; it is a local predicate counterexample. Matching country is not sufficient when the selected region contradicts the candidate. Validate the most specific supported geographic identity and handle synonyms/administrative hierarchy deliberately; do not use an OR across all lineage fields.

### Medium — artwork coverage remains incomplete

Four sampled cards have no image element: one Bon Iver result, one The National result, the Oatly product, and one The Road result. No broken or pending image elements in this sample after the settle interval. Intentional fallbacks preserve identity, but sparse artwork still degrades the visual product. Oatly yields only one direct work; this is honest coverage rather than an obligation to invent four more.

### Remaining explanation/UI limitations

- The arbitrary full-stop truncation is improved: live profile snippets now end with ellipses. These are still descriptions of candidate mood, not always an explanation of the specific shared subject that passed JEV. Do not present descriptive tone as independently verified relevance evidence.
- The Road returned a mix of strict and explicitly looser results. The labels are honest; do not count every card as meeting the strict subject gate.
- Long social links remain starting-point-only with a start-only label/warning; Copy exact link preserves the graph. This is a disclosed limitation, not a silent-sharing regression.
- The short-screen home placeholder is long for its available space and Surprise is icon-only. Reachability/overflow checks passed; these are polish concerns, not claimed accessibility conformance failures.
- Authoritative source records and attributed credits are not proof that each real-world credit is correct. This round did not independently fact-check every Wikidata credit or calculate JEV precision/recall.

## Ten fresh random searches

Stratified random seed `2026102915`, two concurrent isolated browser contexts, real providers, no provider mocks. Entry through the form; identity choice, unique non-source cards, explanations, connections, inspector, saving, reload and Gallery checked.

| Query | Flow | Cards | Loaded artwork | Visible edges |
| --- | --- | ---: | ---: | ---: |
| Bon Iver | Pass | 5 | 4 | 5 |
| The National | Pass | 5 | 4 | 5 |
| Sergio Leone | Pass | 5 | 5 | 5 |
| Neil Gaiman | Pass | 5 | 5 | 5 |
| Oatly | Pass | 1 | 0 | 1 |
| Moonrise Kingdom | Pass | 3 | 3 | 3 |
| The Road | Pass; includes labeled looser tier | 4 | 3 | 4 |
| Celeste | Pass | 2 | 2 | 2 |
| The Wire | Pass | 3 | 3 | 3 |
| Cambridge, England selection | Pass | 5 | 5 | 5 |
| **Total** | **10 flows, no fallback** | **38** | **34** | **38** |

Zero failed/pending images; four absent-image fallbacks. The Edinburgh depth controls are additional and not part of the ten-query totals. The content failures above prevent an “all accurate” verdict.

## Saving, rejection, agent and browser-local retrieval

- The Lighthouse and Dark each passed save → unsave → save, reload persistence, no save-triggered graph growth, Gallery hiding Qloo exploration.
- Resuming The Lighthouse sent exactly one saved signal from that map; retrieved positive anchors did not include another map's liked entity.
- One actual agent run grew the map **3→8**, streamed five additions and reported five.
- Rejected **I'm Thinking of Ending Things**: absent after reload, included in agent dislikes/excludeIds, absent from positive retrieval anchors, not reintroduced. Map **3→2 after rejection, then →7 after exploration**.
- These tests cover those sequences, not simultaneous-tab feedback conflicts or all alternate editions/provider aliases.

## UI, security, server and budget

- Production UI fixture: share initial focus/Tab containment, nested confirmation, description-preserving exact link, Wikidata badge, gallery focus restoration all passed. Recents close is44×44px. Social fixture intercepts external posting/clipboard writes; it is not a relevance test.
- Home reachability/no-overflow at320×568,390×844,768×1024,1440×900,844×390; map overflow at320/390/768/1440 passed.
- Fourteen public-route exposure/input checks passed: sensitive file paths404, unsupported GETs405, null bodies400, foreign Origin403, oversized JSON400.
- Authored shared-map HTML did not execute; javascript links and an HTTP metadata-address image were dropped. No exhaustive injection/SSRF claim.
- Deployed image `2026-10-29-3342031`, health healthy, user=node, read-only rootfs, app port unpublished. Secretfile600/root; Caddy rotation10MB×3. Disk69% used,2.6GiB free. No other EC2s modified.
- Current deployed-public-file scan: **39 files**, zero skipped, **two exact runtime provider values checked, zero matches**. No secret values printed. This does not audit private logs, history or other services, and does not establish key rotation.
- Actual installed dependency inventory: **137 package names**, zero advisories returned by npm registry bulk advisory endpoint. Not proof that no vulnerability exists.
- Offline real-filesystem budget contention:400 admitted,200 capped,zero busy,finalcount400. No provider calls. Does not establish every crash/stale-lock behavior.
- Local lint and **46 individual unit tests** passed. The geography regression fails intentionally on the remaining nested error; passing unit tests must not hide that failure.

## Reproducers and evidence

- `tests/live_queries_round15.py`; `/tmp/throughline-round15-results.json`.
- `tests/live_geography_round15.py`; `/tmp/throughline-round15-geography.json` (failing live regression).
- `tests/geography_predicate_round15.mjs` (synthetic production-helper counterexample).
- Existing state/rejection/UI/security/shared-safety scripts rerun; their `/tmp/throughline-round10-*`, round11 and round14 rejection outputs refreshed.
- Server/runtime review command `b494a583-defd-429e-9d7f-d63964751a1f`.

No new public credential leak found within this scope. Key rotation remains unverified. No production or application changes were made during this review.
