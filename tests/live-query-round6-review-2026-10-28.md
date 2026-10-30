# Sixth discovery audit — 28 October 2026

Application commit: **00ce1e3 — Canonical rejection, kept identity on category clicks, edition-aware adaptations, mobile Discover**.

## Outcome: live recommendation testing is blocked

Ten new names were selected reproducibly with seed **2026102806** before requests began. **All ten actual discovery endpoint requests returned HTTP429 with `Daily limit reached for this feature — come back tomorrow.`** No recommendation-quality pass is claimed.

The app itself serves HTTP200. The blocker is the application's accumulated daily discovery budget, not a refused connection or a demonstrated Qloo/JEV outage. The guard returns before entity retrieval and model scoring. No server restart, quota reset, forwarding-header spoofing, direct-provider replacement search, or guard bypass was performed.

The response has `Retry-After: 3600`; that is not proof that the daily window will actually reset in one hour. The implementation uses a rolling daily counter with a fixed retry header.

## Ten selected queries

| Query | Intended meaning | Actual result |
| --- | --- | --- |
| David Cronenberg | Filmmaker | 429 — blocked |
| Isabel Allende | Novelist | 429 — blocked |
| FKA twigs | Artist | 429 — blocked |
| ASICS | Brand | 429 — blocked |
| Children of Men | 2006 film | 429 — blocked |
| The Overstory | 2018 book | 429 — blocked |
| Undertale | 2015 game | 429 — blocked |
| Station Eleven | 2021 TV series | 429 — blocked |
| Reply All | Podcast | 429 — blocked |
| Marrakesh | Destination | 429 — blocked |

The first two were also attempted in isolated 1440px/390px browser contexts. They never reached a usable map because their initial request was rejected. The long browser batch was stopped once the daily cap was confirmed. The remaining explicit endpoint checks were bounded single attempts, not automatic retries.

## Confirmed live issue: quota exhaustion is presented as an empty discovery trail

The browser displays:

```text
Nothing new from here yet. Try another card or direction.
```

The actual server response is:

```json
{"error":"Daily limit reached for this feature — come back tomorrow."}
```

`discover` reads `data.message` but not `data.error`, so a quota error becomes an apparently unsuccessful recommendation query. This can make users change perfectly valid queries and falsely suspect the ranking algorithm. Category/feed paths also discard the guard's `error` field in favor of generic service copy.

Code: [guard response](../lib/guard.ts), [initial discovery error handling](../app/page.tsx#L291), [category error handling](../app/page.tsx#L283), [Discover feed error handling](../app/page.tsx#L234).

Required correction: preserve the real error category and retry information, and distinguish rate-limited, upstream-failed and genuinely empty results. Do not widen or retry a rate-limited request as though no relevant data existed. The budget limit itself is not claimed as a defect; this local instance has accumulated substantial testing/other usage.

## Offline production-helper counterexamples

These checks run the current production helpers with explicitly synthetic identity fixtures. They make **no provider calls**. They are not presented as actual Qloo suggestions from the blocked live sample.

### 1. Different works with year-qualified identical titles are merged

An existing Wikidata-backed **Shared Title (1996)** movie and a Qloo **Shared Title (2004)** movie are reported as aliases by `isAliasOf`.

`workKey` removes every parenthesized qualifier before comparing names and a broad UI category. It does not retain an identity, year, director or source-work relationship capable of distinguishing independent namesakes.

Code: [workKey and isAliasOf](../app/page.tsx#L69).

Consequence: when this condition occurs in real data, the new alias/rejection filter can suppress a genuinely different work rather than just an edition. This audit does not establish how often the provider returns such pairs.

### 2. An artist and a same-named album are merged

An existing Wikidata-backed artist **Shared Name** and a Qloo album **Shared Name** are also reported as aliases.

`workKey` calls `categoryOf`, which deliberately groups artists, albums and songs together under Artists for browsing. A display grouping is not a canonical entity type. A self-titled album is not the same entity as its artist.

Code: [identity key](../app/page.tsx#L69), [broad display category](../app/page.tsx#L79).

Required correction for both cases: use verified identity/alias relationships and precise entity kinds for canonicalization. Name equality plus a display category is insufficient evidence for deduplication, saving or rejection propagation.

### 3. Colon-subtitled sequels are still mistaken for editions

The production `isEditionOf` returns true for:

```text
source: Voyage: Part One
target: Voyage: Part Two Deluxe Edition
type: video_game
```

Both names are reduced to their text before the colon. The new stricter base-title comparison therefore still ignores the part that distinguishes these synthetic sequel titles.

The previously reported **DOOM → DOOM Eternal Deluxe Edition** counterexample now correctly returns false, and **Disco Elysium → Disco Elysium: The Final Cut** correctly returns true. Preserve those repairs while retaining identity-bearing subtitles.

Code: [edition helper](../lib/search-choices.ts#L40).

## What could and could not be validated

- `npm run test:unit`: passed (one top-level test-file result).
- `npm run lint`: passed.
- The focused offline edge runner reports **three failures out of five checks**; these are intentionally exposed regressions, not passing tests.
- The new source changes preserve category-click IDs, traverse edition-of work identities, rebuild filtered memory preferences, distinguish IMDb name/title links and change Discover controls/stacking. Source presence is not live behavioral verification.
- The rejected-book and Discover regression scripts could not reach their required map states because discovery was capped. Their selector timeouts are blocked prerequisites, not new evidence that the repaired UI controls still fail.
- No new standalone JEV benchmark was run. Previous rounds' successful judgments must not be recycled as current-turn model evidence.
- Saving, rejecting, full exploration, RAG retrieval and new recommendation correctness remain **unverified on this run**, because no new map could be created.
- The interrupted browser runner emitted browser-close/cancellation exceptions during shutdown. Those are test-interruption artifacts, not application JavaScript errors.
- No application code was edited and no production build was run.

## Reproduction and next step

Fresh query runner: `tests/live_queries_round6.py`; bounded endpoint mode: `PYTHONDONTWRITEBYTECODE=1 python3 -u tests/live_queries_round6.py --api-only`.

Offline counterexamples: `node --experimental-strip-types --no-warnings tests/round6-static-edges.ts`. This runner extracts the actual pure UI helper source and compiles it in isolation; it does not duplicate a replacement implementation or mock model responses.

Raw evidence: `/tmp/sideways-round6-review-evidence.json`.

Completion requires an available discovery budget. Obtain approval before resetting the local development budget, since doing so permits more Qloo/JEV requests. Alternatively, rerun after the real daily window expires. Until then, the ten selected queries cannot honestly be certified as returning expected data.
