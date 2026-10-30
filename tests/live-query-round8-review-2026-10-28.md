# Eighth live audit — artwork, connections and ten fresh queries

## Verdict

**The Katy Perry problem is reproduced and is not isolated.** All nine usable maps in the new ten-query sample rendered **zero graph edges**. Kraftwerk and Rosalía each returned five factual works with **zero loaded covers**, just like Katy Perry. Italo Calvino returned four uncovered books. Music-work inspectors also lead to unavailable Qloo expansion without a visible explanation.

After bounded retests, the ten new names produced **eight normal flows, one explicitly selected audience fallback, and one blocked disambiguation flow**. Bergen could not be safely identified from the visible choices. This is not a claim that all ten searches work correctly.

The application changed during this audit: the initial Katy reproduction used `c41c094`; `7371028` then landed with the previous audit's memory, rejection and relationship-wording fixes. The later memory/rejection/music-path checks ran against that newer code. Those fixes passed the focused live rechecks below. No application fixes were implemented by this audit; changes here add or improve diagnostic tests.

## Ten fresh seeded queries

Seed `2026102808`, concurrency two, isolated browser contexts at 390px/1440px. These are new names relative to the preceding ten-query sample. Artwork counts mean actual loaded card images, not merely nonempty URLs.

| Query | Meaning | Cards | Loaded artwork | Graph edges | Outcome |
| --- | --- | ---: | ---: | ---: | --- |
| Kraftwerk | Artist | 5 | 0 | 0 | Typed-form identity/save/reload flow passes; visual regression fails |
| Rosalía | Artist | 5 | 0 | 0 | Typed-form identity/save/reload flow passes; visual regression fails |
| Akira Kurosawa | Filmmaker | 5 | 5 | 0 | Correct-looking recorded film credits; missing connections |
| Italo Calvino | Writer | 5 | 1 | 0 | Four Wikidata-only books without covers; missing connections |
| Lush | Brand | 5 | 4 | 0 | No direct work returned; explicit audience fallback used |
| Perfect Days | 2023 film | 2 | 2 | 0 | Evil Does Not Exist and The Quiet Girl; missing connections |
| Annihilation | 2014 book | 3 | 3 | 0 | Two sequels plus an overlapping omnibus; missing connections |
| Celeste | 2018 game | 1 | 1 | 0 | Dead Cells; a taste/gameplay suggestion, not a factual credit |
| The Allusionist | Podcast | 1 | 1 | 0 | A Way with Words; missing connections |
| Bergen | Intended Norwegian destination | — | — | — | Seven indistinguishable destination choices; no guessed selection |

Totals for the nine usable maps: **32 cards, 17 loaded artworks, zero edges**. Katy Perry was an additional targeted reproduction, not counted among the ten new queries: five cards, zero artwork, zero edges.

The initial two artist URL-start attempts stalled with no discovery request while the development app was being edited. A first typed-form attempt also filled SSR markup before React input handlers attached, leaving Explore disabled. The final typed-form retests explicitly awaited real handler attachment; both passed the functional checks. Those original attempts remain in the raw evidence and are not counted as provider failures or silently erased. No persistent production startup defect is established by these interrupted/pre-hydration runs.

## Confirmed remaining issues

### 1. High — initial graph edges are deliberately skipped by the renderer

Katy Perry's live API returns each work with a real source parent and factual relationship. The rendered SVG contains **zero paths**, not faint or hidden paths. This reproduced on every usable initial map in the new sample, including Kurosawa where all five covers loaded.

At [the graph renderer](../app/page.tsx#L377), the parent lookup searches only `nodes`. The starting reference is stored separately as `root`; first-ring nodes use `parentId: root` in the UI layout. The lookup cannot find their parent and immediately returns `null`. Separately, [CSS hides the seed card](../app/globals.css#L1073).

This is not a JEV relevance error, a Qloo outage or an image-loading failure. Removing the source discovery card also removed the endpoints needed to draw the first graph ring.

Required correction: retain a real, visible source anchor and render root-to-result relationships. It can be a compact context marker rather than an extra discovery card, preserving **five results, not six cards**. Do not fabricate connections between sibling albums simply to draw lines.

### 2. High — verified-work fallback has no artwork-enrichment path

Actual Katy Perry response:

- Witness — `wikidata:Q29948806`.
- Teenage Dream — `wikidata:Q186188`.
- I Kissed a Girl — `wikidata:Q155512`.
- Hot n Cold — `wikidata:Q844214`.
- One of the Boys — `wikidata:Q381122`.

All five have **no image URL**. The browser therefore creates no card image elements; these are not five failed network image requests. Kraftwerk's five records and Rosalía's five records use the same image-free fallback. Calvino's four uncovered books do too.

The [fallback construction](../app/api/discover/route.ts#L114) provides a Wikidata ID, description and classification but no image. Its crosswalk inherits a Qloo image only after an external Wikidata/IMDb identity match. That is an important factual-identity guard, but album search results often lack those IDs: the inspected Qloo album records expose image URLs while their external Spotify object is empty. Several same-title records/editions are returned. Selecting the first cover by title would introduce a new guessing bug.

A bounded source check found:

- Witness's exact Wikidata item has no P18 image but does have MusicBrainz release-group `bded1701-baf2-4066-b76a-49384de006b6`.
- Teenage Dream has release-group `e6f683c9-fc85-412c-a352-d6e411fc2603`; its P18 image is **a logo**, not an album cover.
- I Kissed a Girl has release-group `e31bf349-d257-31e6-852a-401c0c221cbe`; its P18 is also a logo.

Required correction: use identity-bound artwork enrichment, not title-only image search or any P18 image indiscriminately. [The Cover Art Archive API](https://musicbrainz.org/doc/Cover_Art_Archive/API) supports lookup by release-group identity; per-record availability, host safety, caching and attribution still need validation. This audit checked the documented route and existing source IDs, not that every particular release currently has usable art.

When artwork genuinely cannot be verified, use an intentional text/icon fallback. The current huge, clipped category words and initials make missing data look like a broken poster layout. Do not replace correct factual works with unrelated image-rich recommendations.

Reproducer: `tests/live_round8_art_sources.ts`; screenshots in `/tmp/sideways-katy-art-current.png` and `/tmp/sideways-round8-artist-{0,1}.png`.

### 3. High — music-work inspectors become blank discovery dead ends

Live browser checks of **Witness** and **Trans-Europe Express**:

1. Open the verified work from its artist's map.
2. Suggestions return four proposed categories.
3. Availability prefetch sends the precise Wikidata ID, work type and dated description.
4. `/api/discover` returns HTTP **422**, reason **no_qloo_identity**.
5. The main four category buttons disappear. The inspector still shows **Powered by Qloo audience affinity** and **6 more**, without exposing the returned explanation.

The exact response is that the work is a verified credit but Qloo has no matching record to explore from yet. This means a unique matching record was not established; it does not prove no similarly named catalog record exists. The title collisions observed above make guessing unsafe.

[loadCategoryBatch](../app/page.tsx#L291) turns the offered categories into unsupported states. Quiet prefetch suppresses the explanatory notice, and the inspector's category filtering removes those buttons. The remaining unknown categories still look like possible paths even though the same unresolved anchor blocks them too.

Required correction: show an explicit work-level availability state and do not present category navigation as confirmed when its anchor cannot be resolved. If a validated work crosswalk is unavailable, offer a clearly separate action such as the **artist's audience matches**, naming the changed anchor. Never silently claim those matches came from the album.

Reproducer: `tests/live_round8_music_paths.py`. This tests the second-stage journey, not just first-screen card appearance.

### 4. Medium — Bergen's chooser discards available geography

The normal Bergen search exposes seven destination options named **Bergen**, each described only as **Geographic area**, plus a distinguishable 2022 movie. The expected country cannot be established from visible text, so the audit does not choose the first destination blindly.

The provider records do contain geography in `properties.ancestors` and location aliases. Inspected records include Bergen County in New Jersey, Bergen in Germany and Bergen in New York; a compact provider response also identifies the Norwegian record with an alias containing **Vestland, Vestlandet, Norge**. That distinction is not shown to the user.

[detailOf](../app/api/discover/route.ts#L42) looks for a top-level `country` string rather than the returned ancestor/location structure. Its fallback therefore erases the very evidence needed to disambiguate. JEV choice ranking receives the same generic details and cannot reliably resolve this from supplied geographic evidence.

Required correction: include place kind, region and country from actual metadata in both chooser text and ranking evidence. Preserve distinct geographic identities; do not auto-select Bergen County just because it ranked first.

### 5. Medium — an omnibus containing already shown works is treated as a new discovery

Annihilation returns:

1. Authority, the second novel.
2. Acceptance, the third novel.
3. Area X: The Southern Reach Trilogy, volumes 1–3.

[The publisher confirms](https://us.macmillan.com/books/9780374261177/areax/) that Area X collects Annihilation, Authority and Acceptance. Thus the third card overlaps the starting book and both other suggestions. It is semantically relevant, but not a third distinct new work.

[repeatsBookSource](../lib/search-choices.ts#L50) checks slash/ampersand/“and” title fragments. It cannot detect this omnibus's contents from its differently named title or range qualifier. The real returned description even begins by repeating book one's synopsis.

Required correction: separate content-level novelty from subject relevance, using supported collection/edition evidence. Either suppress overlapping bundles in new-work discovery or label them explicitly as collections, without suppressing legitimate sequels. This does not justify lowering JEV thresholds or inventing different-category fillers.

## Additional offline identity risk

The new title/type rejection key fixes the specific Parable alias, but two independent works with the same unqualified title and category still have the same key. The exclusion payload drops source IDs, years and creator evidence when forming that key.

`tests/round8-static-edges.ts` extracts the actual production helpers and reports:

- Different same-title movie fixtures with different IDs/years: **incorrectly share a rejection key**.
- The confirmed Parable provider alias: **correctly shares a key**.
- The actual Annihilation/Area X bundle titles: **not recognized as overlapping**.

Two failures out of three checks. The namesake case is an **offline counterexample**, not a claimed live UI rejection sequence. Canonical identity should distinguish works while recognizing verified aliases; a normalized title alone cannot do both safely.

## JEV check and interpretation

Three newly returned positive pairs plus three deliberately crossed negative controls were scored twice with real JEV and complete provider descriptions/themes/tag selection. Affinity was fixed at 0.95 to isolate semantic qualification. Crossed negatives are test controls, not alleged Qloo recommendations.

- Annihilation → Authority: accepted twice.
- The Allusionist → A Way with Words: accepted twice.
- Perfect Days → The Quiet Girl: rejected twice, subject scores 0.46/0.45.
- All six negative-control decisions were rejected.

Total **10/12 decisions matched the proposed labels**, with no missing scores. The Quiet Girl is a plausible observational-cinema/taste match, but its proposed positive label is not objective factual ground truth. The production initial response did include it; the standalone batch/evidence context differs, so this is not proof that an identical production prompt changed its answer. Keep this as a calibration/recall warning, not a statistical accuracy claim or permission to weaken every gate.

The artwork failures and zero graph paths happen outside JEV; changing its prompt will not fix those defects.

## Previous fixes rechecked live on 7371028

- Resumed-map memory: immediate Children of Men request now contains its own saved novel and paths, not Station Eleven's. The settled control also stays correct.
- Discover-only save: Days of Being Wild persists, graph stays at three cards, and the next request now includes its named positive anchor and summary.
- Rejected Parable alias: server returns an empty book category before insertion rather than the rejected Qloo alias. The map stays at four cards and copy reports no new verified matches, not a false success.
- Source-work wording: the two inspectors now say the reference is based on the source, without duplicated titles.

These are bounded passing reproductions, not proof that all memory/identity edge cases are fixed. The namesake-key counterexample above remains.

## Tests and evidence

- Functional save/reload checks pass on the nine usable maps; Bergen remains unresolved rather than guessed.
- `npm run test:unit`: pass.
- `npm run lint`: pass.
- `tests/round8-static-edges.ts`: two exposed failures, intentionally nonzero exit.
- The new ten-query runner now exits nonzero for visual issues as well as functional failures. A successful Save/Reload flow cannot produce a green overall result when the map has no connections or missing covers.
- No production build or application edits were made by this audit.

Main runner: `PYTHONDONTWRITEBYTECODE=1 python3 -u tests/live_queries_round8.py`.

Artist typed-form check: add `--artists-via-form`. It waits for real input-handler attachment before typing. This is a test readiness condition, not a mock or forced click.

Artwork and music-path diagnostics: `tests/live_round8_art_sources.ts`, `tests/live_round8_music_paths.py`; shared visual capture: `tests/live_visuals.py`.

Raw evidence: `/tmp/sideways-round8-review-evidence.json`; JEV fixtures: `/tmp/sideways-round8-relevance-fixtures.json`. Provider credentials are not included.

Highest-priority next work: restore real source edges, enrich factual works with verified artwork, and make unsupported work expansion explicit. Keep factual identity and recommendation quality intact while doing so.
