# Fifth live discovery audit — 28 October 2026

## Verdict

**Better, but not an all-clear.** Ten new seeded queries produced nine normal initial flows and one explicitly chosen audience fallback. All ten initial inspector checks encountered the already-exhausted suggestions quota. The new fallback UI now keeps unranked category navigation available rather than showing an empty loading panel.

Application commit **feb6b0a — Identity correctness and current feedback** landed during the opening inspection, before the captured direct-result responses. The initial commit read was 46e99de; subsequent inspection and all focused reproductions used feb6b0a. The new relationship wording in the captured initial results also confirms the updated path was running. The application was not changed by this audit.

The new standalone JEV check passed **16/16 judgments on eight labeled pairs**, and a full agent run added exactly five cards while preserving the one saved preference. However, identity, rejection and retrieval defects remain outside that small model test.

## Remaining findings

### 1. High — a rejected work returns under its other provider ID

Visible browser reproduction on a fresh Octavia E. Butler map:

1. Reject **Parable of the Talents**, ID `wikidata:Q3211325`.
2. Open **Parable of the Sower**.
3. Open More categories and wait for the live Books availability check to finish.
4. Choose Books.
5. The map grows from four to five cards, adding **Parable of the Talents (Earthseed, #2)**, Qloo ID `7DEDF979-7343-4B8D-BD58-D335F6B24D92`.

The actual request explicitly includes the original Wikidata ID in `dislikedIds`, `excludeIds`, negative graph-memory anchors and `rejectedIds`. The provider alias still passes. This is the same work, not a separate adaptation.

The new `isAliasOf` suppresses aliases only against cards that remain in the map/Discover saved list. Rejection removes the original card, so that protection no longer has anything to compare against. Feedback, exclusions and memory still use provider-specific IDs.

Code: [map alias check](../app/page.tsx#L70), [rejection](../app/page.tsx#L207), [category exclusions](../app/page.tsx#L279), [ID-keyed feedback](../lib/feedback.ts).

Required correction: persist verified canonical identities and their provider aliases; apply the canonical identity to rejection, saving, insertion, exclusions and memory. A check against currently rendered titles does not implement canonical feedback.

### 2. High — clicking a category can discard the identity that prefetch correctly preserved

The same browser path was tested both quickly and after waiting for availability:

- Prefetch sends `entityId: wikidata:Q3823447`, `name: Parable of the Sower`, `entityType: book` and receives a valid Books result.
- A quick Books click sends only `text: Parable of the Sower` plus the requested category. It does not retain the ID/type.
- When the prefetch has not populated the cache yet, the server returns clarification. The category handler cannot present that chooser and reports **Qloo could not tell which “record” this is, so nothing was guessed.**
- Waiting for prefetch avoids that request because the cached category result is reused. It then exposes finding 1.

This is a real timing-dependent flow failure, not a claim that every category click fails. The primary and expanded category handlers both still convert Wikidata-backed cards into bare-text searches.

Code: [identity-preserving prefetch](../app/page.tsx#L275), [category batch](../app/page.tsx#L277), [category click handlers](../app/page.tsx#L386).

The successful cached path also displays **1 verified book matches added from undefined.** The text-only seed does not include `name`, so the completion message loses its source too.

Required correction: use `directionSeed(selected)` consistently for actual clicks as well as prefetch; share compatible in-flight category work. Cache timing must not decide whether a known identity survives.

### 3. High — a book edition ID hides its available film adaptation, and the empty result is cached without identity versioning

The Road was resolved to the correct-looking 2006 book but linked to **Q125531128**. A public read of the [Wikidata edition item](https://www.wikidata.org/wiki/Q125531128) identifies it as the first edition, with `P629` pointing to the [underlying novel Q1140295](https://www.wikidata.org/wiki/Q1140295).

Observed live behavior:

| Request | Movies answer |
| --- | --- |
| Normal The Road category probe using returned metadata | Empty |
| Same Qloo ID, explicitly supplied verified original-work QID, same category/cache key | Still empty |
| Same Qloo ID and verified original-work QID, different category set (`movie`, `tv_show`) | **The Road (2009), Adapted from The Road** |

The returned film has Qloo ID `475E4B47-7139-4BF9-A0EA-1B737392D0D4`, IMDb `tt0898367`, and Wikidata Q738052. This establishes that the connection is retrievable; the normal request is not evidence that no film is available.

`workQid` accepts the edition QID as the creative-work identity without traversing its edition-of relation. The adaptation cache is keyed only by Qloo seed ID and requested categories; it does not include the resolved work identity or evidence version. Its 24-hour empty entry therefore survives the corrected-identity control until the category key changes.

Code: [work identity](../app/api/discover/route.ts#L122), [adaptation cache](../app/api/discover/route.ts#L133), [based-on query](../app/api/discover/route.ts#L136).

Required correction: resolve edition-to-work relationships before querying adaptations, and include that canonical identity/version in the cache. Do not paper over missing factual recall by weakening JEV or padding with audience matches.

The corrected-QID requests were controlled API diagnostics, not an ordinary UI recovery the user can perform. The initial browser run explicitly chose Try audience matches and received Hidden Brain, Pixies, Stewart Lee's Comedy Vehicle, No Country for Old Men and The Trip. Those were honestly labeled audience overlap; they must not be described as factual adaptations or unauthorized fallback.

### 4. Medium — identity validation remains restricted to creators; a podcast links to its host as if it were the show

Freakonomics Radio's selected record links to [Wikidata Q454515](https://www.wikidata.org/wiki/Q454515), which the live public API identifies as **Stephen J. Dubner**, a person. The [official show description](https://freakonomics.com/about/) distinguishes the podcast from its host.

The new checked identity lookup runs inside creator direct-work retrieval. It does not validate work/podcast identities or the links emitted by `sourceLinks`. Consequently, a correct-looking card can still carry the wrong source entity. This is a metadata/provenance failure; this test did not prove that its two displayed recommendations were wrong.

Code: [creator-only validation](../app/api/discover/route.ts#L91), [work QID trust](../app/api/discover/route.ts#L124), [source links](../app/api/discover/route.ts#L57).

Required correction: distinguish same-entity links from creator/host/source-work relationships for every entity type. Validate type and identity before using a provider ID as evidence.

### 5. Medium — Discover is unreachable on mobile/tablet, and its desktop close control is covered by the header

Real rendered-layout measurements:

| Width | Accessible Discover launcher | Header Discover/Share display |
| ---: | ---: | --- |
| 390 | 0 | none |
| 768 | 0 | none |
| 900 | 0 | none |
| 901 | 1 | flex |
| 1440 | 1 | flex |

There is no alternate visible Discover launcher in these tested map states. The mobile feed workflow therefore cannot begin through the normal UI.

At 1440px the feed opens, but its close button is positioned at x1326, y48, size42×42. Hit testing its center returns the editorial header, not the close button. An actual click retries and times out because the header intercepts it. This is not a failure caused by a forced or synthetic click.

The feed starts at the top of the viewport with z-index70; the fixed 76px header has z-index95. The <=900px rule hides every `.top-share`, which includes both Share and Discover.

Code: [mobile header rule](../app/globals.css#L1128), [header stacking](../app/globals.css#L1065), [feed geometry](../app/discover-board.css#L1).

Required correction: provide accessible compact launchers at small widths, and place the feed below or above the header with a genuinely clickable close control. Both entry and exit must work through normal pointer/touch interaction.

### 6. Low — immediate Unsave removes the positive anchor, but leaves its derived preferences in the request

The principal race fix works: after Save → wait1.5s → Unsave → immediately Explore for me, the request has `likes: []`, no liked cards and **no positive anchors**.

However, the same request still sends `preferredTypes: [movie]` and the removed film's Art house/Romance/Drama tags, alongside the summary No earlier taste memory yet. `liveMemory` filters anchors and rebuilds the summary but does not recompute the derived fields.

This is a consistency gap, not proof that this run displayed an incorrect card. The run was explicitly cancelled before reveal and the map stayed at five cards. The discovery reranker can still consume stale preferred types even when there are no anchors.

Code: [live memory reconciliation](../app/page.tsx#L203), [memory type preference consumption](../app/api/discover/route.ts#L274).

Required correction: rebuild derived preferences from the reconciled anchors and latest explicit feedback, or version the whole snapshot atomically. Retain only genuinely current evidence.

### 7. Medium, code-level regression — edition detection can suppress a different sequel

Direct checks of the production `isEditionOf` function return true for:

```text
Disco Elysium → Disco Elysium: The Final Cut     (intended)
DOOM → DOOM Eternal Deluxe Edition             (different base title)
Resident Evil → Resident Evil 2 Remake          (different numbered title)
```

The function accepts any target beginning with the source's punctuation-stripped prefix if an edition/remake word occurs later. It does not establish that the title before that qualifier is the same work.

Code: [edition heuristic](../lib/search-choices.ts#L40).

These are deterministic code counterexamples, **not** claims that the live ten-query run actually returned and dropped those particular games. The new Disco Elysium live check correctly omitted The Final Cut. Preserve that improvement while comparing canonical base-work identities rather than broad title prefixes.

### 8. Low — IMDb name IDs are emitted under the title URL namespace

The actual audience fallback includes Pixies with IMDb link `https://www.imdb.com/title/nm0686139/`. A name identifier (`nm…`) is not a title identifier (`tt…`); the formatter uses `/title/` for both.

Code: [source URL formatter](../app/api/discover/route.ts#L55).

Required correction: validate the external identifier kind and construct the appropriate name/title URL. This is a link-construction defect, not a claim based on an IMDb bot-block response.

## Ten new queries

Sampling seed: **2026102805**. One query was sampled from each of ten category pools before requests began. Browser contexts were fresh and isolated, with 1440px desktop and 390px mobile checks, concurrency two. Real configured providers were used; no API responses were mocked.

| Query | Initial path | Cards | Returned examples |
| --- | --- | ---: | --- |
| Wong Kar-wai | Direct | 5 | In the Mood for Love, Chungking Express, Fallen Angels, Happy Together, 2046 |
| Zadie Smith | Direct | 5 | White Teeth, On Beauty, NW, Swing Time, Intimations |
| MF DOOM | Direct | 5 | Mm.. Food, Operation: Doomsday, Born Like This, Vaudeville Villain, Take Me to Your Leader; album types retained |
| Converse | Direct | 4 | Chuck Taylor All-Stars, Quick Star, Jack Purcell, Marquis Mills Converse |
| In the Mood for Love (2000) | Affinity | 3 | Chungking Express, Paris Texas, Sunrise |
| The Road (2006 book) | Explicit audience fallback | 5 | No initial qualified set; see edition/adaptation failure above |
| Return of the Obra Dinn | Affinity | 1 | Tacoma |
| Mr. Robot (2015) | Affinity | 4 | Humans, Deus Ex: Human Revolution, Black Mirror, Westworld |
| Freakonomics Radio | Affinity | 2 | Adam Ruins Everything, Invisibilia |
| São Paulo | Geographic | 5 | Nubank Parque, Beco do Batman, Shopping Eldorado, Pinheiros, Farol Santander |

All ten sampled flows passed the harness's card-count/unique-ID/source-context checks, Save without graph expansion, saved persistence after reload without a repeated search, Gallery opening and horizontal page-overflow checks. The fallback is counted separately from the nine normal flows. A flow pass is not independent factual verification of every description, credit, external ID or semantic connection.

Expected years and descriptive identity clues were checked where clarification exposed them. The Obra Dinn result auto-resolved; no unseen year check is claimed. Several selected identities have duplicate provider records and remain chooser-ranking cases, not proof that all aliases are correct.

## New live JEV check

Four positive and four crossed negative pairs, two fresh-cache runs each. Anchor evidence was hydrated from live Qloo entity records. Candidate descriptions came from the current round's actual returned data. Affinity was fixed at .95 to isolate semantic qualification; crossed negatives are not claimed to have been actual Qloo recommendations.

| Anchor → candidate | Expected | Votes |
| --- | --- | --- |
| In the Mood for Love → Chungking Express | Keep | Keep / Keep |
| In the Mood for Love → Deus Ex: Human Revolution | Reject | Reject / Reject |
| Return of the Obra Dinn → Tacoma | Keep | Keep / Keep |
| Return of the Obra Dinn → Happy Together | Reject | Reject / Reject |
| Mr. Robot → Deus Ex: Human Revolution | Keep | Keep / Keep |
| Mr. Robot → Invisibilia | Reject | Reject / Reject |
| Freakonomics Radio → Invisibilia | Keep | Keep / Keep |
| Freakonomics Radio → Happy Together | Reject | Reject / Reject |

Result: zero disagreements with these labels, zero unstable decisions, zero failed judgments. This is a small selected regression sample, not a population accuracy estimate. It does not test identity resolution, factual credit verification, availability of unqueried candidates, canonical exclusions or complete RAG correctness.

## Full agent and Discover action checks

Fresh Wong Kar-wai map, with only In the Mood for Love saved:

- Request contains one liked item and one positive memory anchor, not saves from another map.
- Inspector-confirmed TV shows and Movies are sent as available categories; confirmed-empty categories are also carried.
- The agent tries a confirmed category first and returns My Mister from the saved film.
- It later returns Days of Being Wild, Comrades: Almost a Love Story, Yi Yi and As Tears Go By from Happy Together.
- The stream reports five additions; the graph grows from five to ten, and Saved remains one.

One saved preference is not a one-result limit. Five recommendations from one save is expected behavior when five candidates qualify. This run did not reproduce the earlier count discrepancy.

At desktop width, a fresh In the Mood for Love Discover feed also passed:

| Action | Graph cards | Saved |
| --- | ---: | ---: |
| Before feed interaction | 3 | 0 |
| Save Days of Being Wild | 3 | 1 |
| Reject Wild Strawberries | 3 | 1 |
| Add saved Days of Being Wild to map | 4 | 1 |

No horizontal page overflow was detected. The close-control failure and missing mobile launcher are recorded separately; this is not claimed as a complete mobile feed-flow pass.

## Confirmed repairs from the new commit

- The Jungle Book remains literal and offers the 1894 book plus film variants; The Artist offers the 2011 film instead of resolving The.
- Up and U2 now offer real identities in the browser. Up movie resolves the 2009 film and returns connections; U2 band resolves the Irish band intent rather than an empty chooser.
- Iceland country resolves Ísland and returns five geographically linked places.
- Aphex Twin's incorrect linked QID is recovered for direct retrieval; the live direct response includes Selected Ambient Works 85–92, Drukqs and Selected Ambient Works Volume II.
- Ishiguro's Remains of the Day film now says adapted from a work by, not Screenplay by. Screenwriter statements are qualified as Wikidata statements.
- Immediate Unsave no longer sends the removed card as a positive anchor. Derived-field residue remains as finding6.
- The agent receives inspector availability. Its full run used a confirmed category first.
- Quota-limited suggestions render explicit unranked category navigation rather than an indefinitely checking empty panel. Ranking itself remains unavailable while capped.
- A null card request returned400 early in the focused checks. A later repeat returned429 after the accumulated card quota was reached; it cannot be used as another validation result.
- All four former numeric-margin boundary examples now pass consistently.
- The live Disco Elysium result no longer includes The Final Cut; its sole returned card was The Forgotten City. This is not a claim that every edition relationship is classified correctly.

## Validation, artifacts and limits

- `npm run test:unit`: passed (one top-level test-file result).
- `npm run lint`: passed.
- Application code was not edited by this audit. No production build was run.
- The local instance's accumulated suggestions quota remained exhausted throughout the sample; the card feature later reached its daily cap too. No quota reset, server restart, forwarding-header spoofing or guard bypass was used.
- A reused round-four script completed its Up/U2 browser checks but timed out waiting for a Her map. A later compact Her endpoint check resolved the expected film and returned four results. The old script's unfinished memory stage is not counted as a passed test; the Wong Kar-wai feedback script supplies the actual completed memory/agent check.
- The first alias test did not click Books because the fallback UI moved it under More categories. Corrected visible-control tests cover both the quick-click failure and the completed-prefetch rejection leak.
- The first Discover script stopped because the launcher was hidden on mobile. The desktop follow-up exposed the covered close button. The final run records hit testing rather than forcing that obstructed click, preserving the successful action counts without claiming exit succeeded.

Reproduction scripts: `tests/live_queries_round5.py`, `tests/live_round5_api.py`, `tests/live_round5_paths.py` (also run with `--wait-for-availability`), `tests/live_round5_feedback.py`, `tests/live_round5_discover.py`, and `tests/live_round5_relevance.ts`. The semantic script consumes `/tmp/sideways-round5-relevance-fixtures.json`, built from this sample's returned records.

Raw evidence: `/tmp/sideways-round5-review-evidence.json`. It contains isolated-browser/API observations, not credentials or the user's browser storage.

Next priorities: canonical feedback/exclusions; identity-preserving category clicks; edition-to-work resolution with identity-aware caching; then complete Discover entry/exit and consistent memory snapshots. The tested model decisions do not repair failures in those surrounding layers.
