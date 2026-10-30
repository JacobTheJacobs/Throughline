# Additional live discovery review — 28 October 2026

## Verdict

Not all issues are fixed. Ten additional randomly sampled queries produced **9 technical flow passes and 1 failure**, but the deeper identity review found another serious failure hidden inside a passing flow. A browser flow passing is not proof that the intended reference was offered or that every recommendation is semantically correct.

This was a review, not another application-fix pass. Only audit scripts and this report were changed in this turn; earlier application changes were preserved.

## Test scope

- Live local application at `http://127.0.0.1:5173`, using actual configured Qloo, Wikidata and JEV providers; no mocked API responses.
- Reproducible stratified random sample, seed `2026102802`, one previously untested query per group. Failed samples were not replaced.
- Fresh isolated browser storage per sampled query; desktop 1440px and mobile 390px. No user browser state was changed.
- Each successful initial flow checked source context, 1–5 unique non-source cards, explanations, card opening, saving without graph expansion or discovery requests, saved-state reload without a repeated search, Gallery navigation, and horizontal overflow.
- Follow-up browser tests exercised a saved Wikidata-only book, category expansion, the agent, and save isolation across maps in the same browser.
- A separate ordinary flow saved Blade Runner 2049, rejected The Three-Body Problem, used Movies, ran the agent, and opened Discover.
- Two additional direct, read-only Qloo searches distinguished missing provider data from application filtering. Category filtering follows [Qloo's documented `types` search parameter](https://github.com/qloo/docs-public/blob/main/reference/get-search.md).

## Sample results

| Query | Initial browser flow | Cards | Content / follow-up observation |
| --- | --- | ---: | --- |
| Bong Joon-ho | Pass | 5 | Parasite, Mickey 17, Memories of Murder, Snowpiercer, Okja; direct credits, no audience scores. |
| Haruki Murakami | Pass | 5 | Correct book titles, but all five are Wikidata-only and continuation fails; see findings 3–4. |
| Nina Simone | Pass | 5 | Musical credits distinguish albums and songs. Feeling Good remains neutral `work` when classification is insufficient; this is not guessed to be an album. |
| IKEA | **Fail** | — | All eight offered meanings are store places; the brand is missing despite existing in Qloo. |
| Arrival | Pass | 4 | Blade Runner 2049, The Three-Body Problem, Nocturnal Animals, Life. A flow pass is not independent validation of all four thematic connections. |
| The Dispossessed | **Technical pass; intended-book coverage failure** | 2 | Offered the 2013 Szilárd Borbély book and a detective novel, but hid Le Guin's 1974 work. The resulting Hungarian-fiction recommendations belong to the selected namesake, not Le Guin's novel. |
| Portal 2 | Pass | 2 | Portal: Still Alive and Portal; source links include incorrectly constructed Metacritic movie URLs. |
| Succession | Pass | 2 | The White Lotus and Dopesick; labeled as audience affinities, not factual credits. |
| Radiolab | Pass | 2 | Last Week Tonight with John Oliver and Invisibilia; audience-affinity labels. |
| Kyoto | Pass | 5 | Five places, labeled Located in and without audience scores. |

The reported 5.4–10.3 seconds for passing samples cover the complete automated search/save/reload/Gallery flow, not isolated API latency. No JavaScript errors or HTTP-error warnings were recorded in those nine initial flows.

## Findings, in priority order

### 1. High — exact-title filtering removes the intended book before JEV can rank it

Reproduction: search **The Dispossessed**. The application offers only the 2013 book and `The Dispossessed (Detective Jeff Rickman #1)`.

The same unfiltered Qloo search actually returns **The Dispossessed: An Ambiguous Utopia**, 1974, entity `C75EA743-C08D-4DBF-B456-AC6B71AC14AC`, as its first record. The exact-name pool takes precedence, while the related-name check only accepts a literal space after the query. A colon subtitle is excluded. JEV never sees that candidate.

Le Guin's [official book page](https://www.ursulakleguin.com/dispossessed) confirms the original title and year. This is a verified identity-coverage defect, not evidence that the Hungarian-fiction matches are wrong for Borbély's book.

Code: [search pool and choice gating](../app/api/discover/route.ts#L165), [literal-space prefix matcher](../app/api/discover/route.ts#L40), [title matching](../lib/search-choices.ts#L10).

Required correction: retain legitimately qualified titles in disambiguation and compare author/year/linked identity; do not silently force the best-known namesake or merge all same-title works.

### 2. High — stores saturate brand resolution

Reproduction: **IKEA** offers eight same-name `place` records with similar descriptions and no useful location distinction. **IKEA brand** still does not offer the brand.

A documented type-filtered Qloo search returns brand entity `7E9A2E74-1CB5-43E9-8B74-69CA8283BFBD`, linked to Wikidata `Q54078`. The record exists; a single untyped top-ten search fails to retrieve it for the chooser. JEV cannot recover an entity absent from its candidate pool.

Code: [untyped top-ten initial search](../app/api/discover/route.ts#L165), [eight-choice display limit](../app/api/discover/route.ts#L173).

Required correction: resolve explicit category intent and use a bounded, conditional type-specific lookup when same-name locations crowd out other meanings. Do not request every category speculatively or pretend an individual store is the brand.

### 3. High — Wikidata-only category exploration swallows clarification

Reproduction: Haruki Murakami → **Norwegian Wood** → save → **Books**.

- The displayed source is correctly `wikidata:Q751348`, book, description `1987 novel by Haruki Murakami`.
- `directionSeed` drops this identity and type, sending only `{text:"Norwegian Wood"}`.
- The server responds `mode:"clarify"`, offering the book, film, artist and albums.
- `loadCategoryBatch` ignores the response mode and interprets missing availability as `pending`.
- Clicking Books repeats the ambiguous request and reports **Qloo is still searching for book**, although the server already completed and asked a question. The map stays at five cards.

The real Qloo book `AB5E9CA9-E7A4-4D68-A641-FE2276C1C103`, year 1987, is visible in that clarification response. A safe crosswalk is needed, not an unqualified name search or automatic namesake selection.

Code: [identity dropped](../app/page.tsx#L256), [response-mode handling](../app/page.tsx#L261), [false pending notice](../app/page.tsx#L264).

### 4. High — the agent silently excludes every Wikidata-only saved anchor

Same Murakami map: five valid displayed works, one saved book. Click **Explore for me**.

The live stream contains only:

```
Scoring 0 discoveries with 1 saved signal.
No strong new matches this time.
```

No candidate evaluation occurred. The agent explicitly filters out every `wikidata:` ID, without attempting a verified Qloo crosswalk or explaining that the anchors cannot currently be expanded. It reports a relevance failure when the actual problem is identity support.

Code: [agent pool filter](../app/api/agent/route.ts#L67).

Required correction: share identity resolution across manual categories, agent and Discover, or show an explicit unsupported-anchor state with an actionable path.

### 5. Medium — the agent still truncates the evidence used by the shared relevance gate

The inspector/category path sends full bounded descriptions. In contrast, the browser's agent payload truncates each card to **240 characters**; the server cannot recover the missing tail by allowing 300. That short string becomes `parentDescription` in the internal discovery request. `anchorFor` trusts a nonempty supplied description rather than hydrating a richer record.

Consequently, increasing the shared evidence formatter to 1600 characters does not fix the agent path: subject/theme information after a cast-and-credits prefix can still disappear. Parent selection uses 180 characters and candidate taste scoring 160. This is a code-confirmed inconsistency; this audit does not assign a measured accuracy loss specifically to truncation.

Code: [browser agent payload](../app/page.tsx#L229), [server truncation](../app/api/agent/route.ts#L48), [forwarded parent evidence](../app/api/agent/route.ts#L81), [anchor hydration condition](../app/api/discover/route.ts#L144).

Required correction: use one bounded evidence contract and hydrate canonical evidence when necessary, rather than forwarding a display excerpt as the authoritative anchor description.

### 6. Medium — unknown category availability is advertised as confirmed matches

The Norwegian Wood inspector displays **6 more · 10 with matches**, even though its availability request returned clarification and confirmed no category. Unknown, failed and pending categories are counted because only `empty` and `unsupported` are excluded.

Code: [category counts and chips](../app/page.tsx#L367).

Required correction: count only `available` as with matches; show other states truthfully and handle identity clarification separately from pending work.

### 7. Medium — exhausted Discover feed remains a repeated-request dead end

In the ordinary Arrival flow, the Movies expansion added three movie cards from Blade Runner 2049. The agent then added five recommendations while the Saved count stayed at one.

Opening Discover next returned HTTP 200 with `reason:"no_relevant_matches"`, no failed or pending provider categories, and zero cards. The UI still displayed **Your next discoveries are waiting**, **Find discoveries**, and repeated Load more controls. It discards the server's reason and does not record a terminal result for the unchanged anchor/exclusion/preferences signature.

This audit observed the initial empty request and inspected the retry code; it did not repeatedly press Load more to spend duplicate calls.

Code: [feed response handling](../app/page.tsx#L219), [unchanged empty UI](../app/page.tsx#L340).

Required correction: a clear exhausted state, bounded negative-result caching, and an explicit different-anchor action. Do not pad with unrelated data or silently switch recommendation semantics.

### 8. Medium — graph-memory reranking is not consistently wired into discovery paths

There is browser-local graph retrieval: feedback is scoped by map, the latest feedback wins, and retrieval collects one-hop graph paths. However, category batches, Discover feed requests and agent internal discovery calls do not pass that retrieved `memory` context. They still use explicit taste fields, so they are not wholly unpersonalized; they are not the same graph-memory pipeline as `requestDiscoveries`.

Also, `requestDiscoveries` sends the nonempty default summary **No earlier taste memory yet**. The server tests only whether the summary is nonempty, so a candidate set larger than one can trigger an unnecessary memory-reranking JEV call even with zero positive/negative anchors or graph evidence.

Code: [graph-memory retrieval](../lib/taste-memory.ts#L44), [generic request context](../app/page.tsx#L187), [category request](../app/page.tsx#L261), [feed request](../app/page.tsx#L219), [agent internal request](../app/api/agent/route.ts#L81), [memory-reranking condition](../app/api/discover/route.ts#L242).

Required correction: explicitly define which actions are anchor-only versus memory-personalized, reuse the scoped context where intended, and skip memory reranking when there is no substantive memory.

### 9. Low — generated evidence URLs use the movie route for non-movies

Portal and Portal: Still Alive returned Metacritic URLs of the form `/movie/1400040389/` and `/movie/1400054042/`. The source formatter hardcodes `/movie/` regardless of entity type and assumes the provider ID is a URL slug.

Code: [source-link formatters](../app/api/discover/route.ts#L52).

This is a construction defect; HTTP availability of each external page was not tested. Existing source scores were not independently revalidated.

Required correction: construct only supported type-aware links with valid slug/URL evidence; omit unsupported links instead of manufacturing a route.

## What worked

- Saving in the nine successful initial flows did not add graph nodes or trigger discovery requests; one saved item stayed one after reload.
- Starting Arrival in the same browser after saving a Murakami book displayed Saved 0 and sent no inherited liked IDs or positive memory anchors. No cross-map save leakage was reproduced.
- The ordinary Movies expansion reused prefetched results and added three movie cards without a new click-time request. This is expected cache reuse, not missing testing.
- The ordinary agent added five recommendations while one saved reference remained one. Recommendation batch size and saved-reference count are different quantities.
- The subsequent Discover request included the rejected Three-Body Problem ID in its exclusions and the one loved movie as its anchor; it did not return the rejected ID.
- Unit suite passed again during this review.

## Accuracy limits and audit artifacts

The 10-query harness originally called The Dispossessed a technical pass because it only matched title/type, not an expected author/year. This review deliberately corrects that interpretation. Future entity tests need expected identity fields, not simply nonempty cards and matching category.

The ordinary streamed agent completed in the UI and subsequent graph exclusions reflected the five additions. Playwright could not retrieve that particular streamed response body through CDP; its individual recommendation contents are therefore **not** claimed independently audited. The Murakami stream was captured successfully.

The existing labeled live JEV benchmark was rerun with **24 pairs, twice each**, using fresh cache keys: precision **1.00**, recall **0.85**, pair-level majority accuracy **0.92**, **1 unstable pair**, **0 failed calls**. No labeled negatives passed, but Wolfwalkers from Studio Ghibli passed once and failed once; Lawrence of Arabia from Dune failed both times. A 1–1 tie is treated as a rejection by this benchmark. Its command exited successfully because these results fall within its current tolerances; that is not zero-defect accuracy.

This small benchmark tests the gate with preselected pairs, not retrieval coverage or title disambiguation. A gate pass cannot repair hidden candidates or lost identity. No new relevance labels were added in this turn, and the acceptance thresholds were not changed.

Reproduction scripts: `tests/live_queries_extra.py`, `tests/live_queries.py`, `tests/live_deep_review.py`.

Raw fresh-browser evidence (no credentials): `/tmp/sideways-extra10-20261028.json` and `/tmp/sideways-deep-review-20261028.json`.
