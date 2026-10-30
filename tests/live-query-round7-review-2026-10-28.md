# Seventh live discovery audit — 28 October 2026

## Verdict

**Ten live searches produced usable maps, but this is not an all-clear.** The previous attempt at these ten names was blocked before retrieval; this run completed it after the explicitly authorized development-cap increase. Nine searches opened their normal flow; ASICS required explicitly choosing the honestly labeled audience fallback. No quota errors occurred in the ten-query browser batch.

The most important newly reproduced defect is **cross-map stale GraphRAG memory**. Saved counts remain map-local, but immediately exploring a resumed map can send another map's positive anchors and discovery paths. A separate Discover-only save persists successfully yet fails to reach the next request's named graph-memory context.

The main browser run used application commit `2441a99`. During the audit, `c41c094` landed, changing chooser presentation/artist lookup and committing the previously authorized cap change and two audit scripts. The later state/feed-memory reproductions and validation ran against `c41c094`. Those changes do not modify the defective memory, alias, adaptation or link-validation paths described below. This audit did not implement application fixes or reset/bypass quotas.

## The ten-query sample

Seed `2026102806`, one selection from each category pool, concurrency two. Browser contexts were isolated from the user's browser; initial widths were 390px or 1440px.

| Query | Resolved meaning | Initial discoveries | Observed result |
| --- | --- | ---: | --- |
| David Cronenberg | Filmmaker | 5 | The Fly, Videodrome, Eastern Promises, A History of Violence, Naked Lunch; recorded directing relationships |
| Isabel Allende | Writer | 5 | Two film adaptations and three authored books; multiple same-name person records were offered |
| FKA twigs | Artist | 5 | Five albums, correctly classified as albums rather than songs |
| ASICS | Brand | 5 after explicit fallback | No verified direct work returned; user-controlled audience fallback returned sports/fitness-related affinities |
| Children of Men | 2006 film | 4 | Source novel plus three audience/subject recommendations; inspector duplicates the reference title |
| The Overstory | 2018 book | 1 | North Woods; not padded to five with weaker results |
| Undertale | 2015 game | 3 | Two Deltarune chapter records and Omori; relationship/identity problems below |
| Station Eleven | 2021 series | 4 | Source novel plus three series; inspector duplicates the reference title |
| Reply All | Podcast | 2 | Note to Self and The Chaos Machine |
| Marrakesh | Destination | 5 | Five places returned within the geographic boundary |

The raw browser summary is **7 FLOW_PASS / 1 FALLBACK / 2 FAIL**. Both failures were the real duplicated-explanation defect, not failed retrieval. Focused follow-up checks completed saving/reload for both affected cases without suppressing that defect. All ten therefore reached usable maps and completed the save/persistence checks across the combined runs. A browser flow pass does not independently prove every recommendation or external link correct.

Initial responses contained 39 discoveries in total. Subsequent searches can return fewer qualifying cards; this audit does not require inventing or padding results to reach five.

## Confirmed findings

### 1. High — immediately exploring a resumed board sends another board's memory

Normal browser reproduction, repeated twice with real persisted feedback:

1. Open Children of Men, save its source novel, reload, and allow memory to settle.
2. Open Station Eleven, save its source novel, reload, and allow memory to settle.
3. Go Home and resume Children of Men through Recent explorations.
4. Immediately click Explore for me. Cancel before reveal.

The captured request contains:

- `root.name`: **Children of Men**.
- `likes`: **The Children of Men**, ID `F1D31C43-7C9C-4CBA-B103-B2C46B6B0F81`.
- `memory.positiveAnchors`: **Station Eleven**, ID `23E536B4-9185-4C01-AE22-2D65A8C9CECC`.
- `memory.recentPath`: **Station Eleven → Station Eleven**.
- `memory.summary`: the Station Eleven board's saved signal and themes.

A second request after 1.2 seconds has the correct Children of Men positive anchor and path. This is a confirmed hydration race, not persistent contamination of the saved-count UI. The diagnostic requests were canceled before graph changes; this establishes wrong data reaching the agent, not which particular recommendations that contaminated run would ultimately choose.

Cause: the debounced [memory refresh](../app/page.tsx#L135) updates a shared `memoryRef` only after 500ms. Resume changes the root immediately without invalidating that ref. [liveMemory](../app/page.tsx#L210) retains positive anchors absent from the current map, so it does not remove another board's anchors. Explore consumes that ref before current-map hydration finishes.

Required correction: bind memory snapshots to a map ID/generation, invalidate on every root transition, and obtain a current-map snapshot before sending an exploration request. An empty/current snapshot is preferable to foreign-board evidence.

Reproducer: `tests/live_round7_state.py`, stages `restored-map-memory` and `restored-map-memory-settled`.

### 2. Medium — a Discover-only save does not refresh the named GraphRAG context

Fresh In the Mood for Love map:

1. Open Discover and save **Days of Being Wild**, without Add to map or Reject.
2. Wait 1.5 seconds; read-only IndexedDB inspection confirms the `love` event persisted under this map's session ID.
3. Click Load more picks.

Observed:

- Saved count is one; graph remains at three cards, as intended.
- The next request's `taste.likedIds` correctly includes Days of Being Wild.
- Its `memory.positiveAnchors`, `preferredTypes` and `preferredTags` are all empty; summary still says **No earlier taste memory yet.**

This is **partial personalization**, not an entirely ignored save: ordinary type/tag taste signals are present. However, named graph-memory retrieval/reranking does not see the newly saved entity. The [memory effect](../app/page.tsx#L135) depends on root, graph nodes and selected card, not Discover-only feedback. [saveFeedItem](../app/page.tsx#L241) persists the event without changing those dependencies; [loadDiscoverFeed](../app/page.tsx#L238) consumes the stale ref.

Required correction: refresh memory from explicit feedback revisions or retrieve it at action time; preserve the rule that saving alone does not create graph nodes.

Reproducer: `tests/live_round7_feed_memory.py`. No response or model scores were mocked.

### 3. High — prefix/name checks still accept a different entity as the source

The live Undertale response includes **Omori** linked to `Q130723601`. A batched primary-source read identifies that item as **OMORI Multiplayer RP**, not the original game described by the card. The item is a video game, so the human-versus-work check cannot catch it. The [Wikidata link validator](../app/api/discover/route.ts#L181) accepts name prefixes in either direction, allowing this different game through.

There is also a whole-work/part identity ambiguity: **Deltarune: Chapter 1** and **Deltarune: Chapter 2** both carry `Q58045522`, whose Wikidata record identifies the overall **Deltarune** game. The [adaptation crosswalk](../app/api/discover/route.ts#L151) takes the first matching external ID and attaches the whole work's recorded relation to Chapter 1. That external ID alone cannot establish a unique chapter identity.

The additional bounded Up regression exposed another source mismatch: **Long Way Up** links to [Long Way Round on Letterboxd](https://letterboxd.com/film/long-way-round/). Only Wikidata receives the current response-level identity check; other provider links can still name a different work.

Required correction: distinguish exact entity, edition, chapter/part, namesake and related-work links. Do not treat prefix equality as verified identity. Drop unverifiable source links or present their actual relationship instead of guessing a replacement. Correct source identity is separate from JEV semantic relevance.

### 4. Medium — every P144 relation is upgraded to “Verified adaptation”

Undertale returns **Deltarune: Chapter 1 — Adapted from Undertale**, labeled **Verified adaptation (Wikidata)**. The code maps every returned [P144 edge](../app/api/discover/route.ts#L148) to an adaptation label, then [assigns the verified-adaptation source](../app/api/discover/route.ts#L166).

[Wikidata's P144 definition](https://www.wikidata.org/wiki/Property:P144) covers broader bases/derivatives/inspiration, not only a narrative adaptation. The [official Deltarune FAQ](https://deltarune.com/help/) describes a different world and a new story while acknowledging connections. That supports a connection, not the stronger assertion that its story adapts Undertale. Likewise, the Up check labels Dug Days an adaptation, while [Pixar describes shorts following Up's dog](https://www.pixar.com/dug-days).

Required correction: retain a conservative **Based on — recorded in Wikidata** relationship unless more specific evidence establishes adaptation, spin-off, sequel or another relation. Direct graph edges bypass semantic scoring intentionally; their provenance and wording must therefore be accurate on their own.

### 5. Medium — rejected aliases still consume category requests and create false availability

Fresh Octavia E. Butler map:

1. Reject **Parable of the Talents**, `wikidata:Q3211325`.
2. Open Parable of the Sower and click Books.

Both actual category requests preserve the selected source ID/type and explicitly send the rejection in exclusions, disliked IDs and negative memory. The API nevertheless returns the same work as **Parable of the Talents (Earthseed, #2)** under Qloo ID `7DEDF979-7343-4B8D-BD58-D335F6B24D92`, with `availability.book: available`.

The updated canvas alias filter now correctly blocks insertion: the map stays at four cards. But the user sees **0 verified book matches added from Parable of the Sower.** The button remains retryable against an allegedly available category. This is an improvement over the earlier rejected-card resurrection, but it is not canonical rejection across the retrieval pipeline.

The server's [exclusion set](../app/api/discover/route.ts#L200) filters provider IDs rather than verified alias identities. The category cache stores availability before client insertion filtering; [completion copy](../app/page.tsx#L290) uses the resulting zero insertion count.

Required correction: apply canonical rejection before availability and candidate scoring; derive category status from insertable results. Distinguish already shown/rejected results from successful additions, without adding repeat requests or padding with other categories.

### 6. Medium — retrieved prose itself contains incorrect factual evidence

The real Qloo entity record hydrated for Station Eleven says it is **directed by Patrick Somerville** and calls it a **six-part drama**. [The producer's official announcement](https://press.wbd.com/us/media-release/hbo-max/daniel-zovatto-and-lori-petty-star-max-original-station-eleven) instead describes ten episodes, created/showrun by Somerville and directed by Hiro Murai. [The publisher's announcement](https://global.penguinrandomhouse.com/announcements/watch-the-trailer-hbo-max-adaptation-of-emily-st-john-mandels-station-eleven/) also separates Murai's directing from Somerville's showrunner role and lists the ten-episode rollout.

The provider record is supplied as descriptive evidence to the relevance scorer. This audit did not prove those wrong credits caused a specific wrong recommendation, but it demonstrates that retrieved text is not necessarily factual ground truth. JEV scoring supplied prose cannot repair its provenance.

Required correction: keep provider editorial descriptions separate from verified structured credits; do not represent every retrieved sentence as verified. Corrections require reliable source evidence, not asking a model to invent replacement facts.

### 7. Low — source-work explanations repeat the reference title

Actual inspector text:

- **Source work of Children of Men Children of Men.**
- **Source work of Station Eleven Station Eleven.**

`Source work of <name>` already contains its source title, but [directConnectionReason](../lib/direct-connections.ts#L20) recognizes only `Source for` and appends the title again. The initial automated failures detected this real presentation defect. Follow-up mobile checks showed saving/reloading still works for both cases.

Required correction: use structured relationship direction or handle the source-work label consistently, including restored maps and brief exports.

## JEV calibration warning — not a broad accuracy claim

Four newly returned positive pairs and four explicitly cross-paired negative controls were scored twice with real JEV. The full-evidence runner hydrates real Qloo descriptions/themes and uses the actual production `topTags` helper. Affinity is deliberately fixed at 0.95 to isolate semantic qualification; crossed negatives are **not** claimed to be actual Qloo recommendations.

- Six of eight positive decisions passed.
- All eight negative decisions were rejected.
- **Station Eleven → Y: The Last Man** scored subject 0.54 and 0.55, below the production 0.60 threshold, despite both records describing rebuilding society after a population catastrophe.
- Total: **14/16 decisions matched the test's intended labels**, with no missing scores. This small, deliberately selected sample is not a population accuracy estimate.

The initial live Station Eleven response did include Y: The Last Man. The standalone paired benchmark uses a different candidate batch and hydrated evidence, so this does **not** prove nondeterminism with an identical production prompt. It exposes a potential recall/calibration weakness that deserves labeled evaluation, not a blanket lowering of the relevance threshold.

An initial description-only helper also produced 14/16, but omitted full provider themes/tags. It was not relied on alone: the newer full-evidence runner reproduces the two misses. Both sets of supplied evidence and scores are retained.

Reproducer: `node --env-file=.env.local --experimental-strip-types --no-warnings tests/live_round7_relevance.ts`, using `/tmp/sideways-round7-relevance-fixtures.json`.

## What passed and what remains bounded

- Main ten-query run: real providers, no HTTP quota errors; creator/work/place identities were resolved before graph creation.
- Save did not expand the graph or start a discovery request; saved state survived reload. Follow-up completed these checks for the two duplicate-copy cases too.
- Immediate unsave: outgoing agent request had zero positive anchors, zero preferred tags/types and Saved 0.
- Canceled agent: no reveal and no graph mutation.
- Completed Wong Kar-wai agent run: **one saved item, five new recommendations**, graph 5 → 10, Saved remains 1. Output budget is independent of saved-item count.
- Discover Save/Reject/Add separation: graph 3 → 3 → 3 → 4, Saved remains 1. Only Add to map inserted a node.
- Discover launcher accessible at 390, 768, 900, 901 and 1440px. Desktop close button passed center hit testing and normal click. No horizontal overflow in these checks; this is not a full mobile accessibility certification.
- Rejected alias no longer reappears on the canvas; retrieval/availability defect remains as described.
- Quick category clicks preserve Wikidata-backed identity, unlike the earlier regression.
- All three Road edition/adaptation probes now return the 2009 film, including the normal raw-edition request and same-key corrected-identity control.
- Literal/typed query checks returned usable responses for The Jungle Book, The Artist, Up movie, U2 band, Iceland country and Her. This verifies endpoint/identity flow, not the relevance of every returned result.
- Aphex identity repair, Ishiguro role wording and Disco Elysium edition exclusion returned live data. Existing imported screen-credit caveats still apply; not every released credit was independently researched here.
- Malformed `null` card request: HTTP 400, not a crash.
- Five previous offline identity/edition counterexamples: all pass.
- `npm run test:unit` and `npm run lint`: pass. No production build was needed for this audit-only work.

## Evidence and reproduction

Raw responses/request bodies, isolated-browser observations, primary-source identity reads and model scores: `/tmp/sideways-round7-review-evidence.json`. No credentials are included.

New focused scripts: `tests/live_round7_state.py`, `tests/live_round7_feed_memory.py`, `tests/live_round7_relevance.ts`.

Existing runners reused: `tests/live_queries_round6.py`, `tests/live_round5_paths.py`, `tests/live_round5_feedback.py`, `tests/live_round5_discover.py`, `tests/live_round5_api.py`, and `tests/round6-static-edges.ts`.

Application fixes should prioritize map-bound/current memory and canonical identities. Raising the cap enabled testing; it did not fix relevance or provenance. Do not weaken gates, manufacture factual relationships, or silently switch categories to make the result count look healthy.
