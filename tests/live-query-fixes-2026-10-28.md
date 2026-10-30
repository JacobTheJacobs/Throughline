# Discovery fixes — live validation, 28 October 2026

## Outcome

All 20 original audit queries now reach a map and pass card opening, saving without expansion, saved-state reload, Gallery navigation, unique non-source card limits, and horizontal-overflow checks.

The complete same-20-query live suite finished with 20 FLOW_PASS, 0 fallbacks, and 0 failures. A final source-bundle suppression change was additionally verified with a focused 1984 browser rerun; the row below uses that later result. Provider-backed tests used fresh isolated browser contexts, not mocks. No tested flow reported JavaScript errors or HTTP-error warnings. Ambiguous names still deliberately offer choices; the identified record ranks first.

## Fixes made

- Search scoring now includes candidate descriptions, years, popularity and linked identity. Deterministic evidence quality prevents an opaque namesake from outranking an identified creator merely through an indistinguishable model question.
- Same entity IDs are deduplicated; contradictory category metadata is filtered. Corporate legal-name variants and work-title qualifiers remain selectable instead of disappearing behind exact-name songs and places.
- Verified work fallbacks read Wikidata classification and descriptions. Albums are albums, songs remain songs, and consoles are products. A musical credit without classification stays a neutral work instead of being guessed to be a song. Older stored factual explanations are repaired on restoration.
- JEV receives complete bounded descriptions and thematic evidence instead of a 300-character cast/credits prefix. Evidence hashes include the longer content and themes. The existing acceptance thresholds remain unchanged.
- City/country records use Qloo's strict geographic boundary filter and show “Located in”, without an audience-affinity score. Locality aliases map to Destinations.
- Empty/unsupported results and temporary verification failures have explicit inline recovery. There is no silent audience fallback or invented padding; the existing map and saves remain intact. Temporary failures have a user-triggered retry.
- Adaptations no longer repeat the reference title. Factual connections retain priority when laid out alongside affinity recommendations.
- Saved-map restoration recognizes legal-name and title aliases. Going Home clears stale seed/shared-map URL state.
- Save no longer immediately repeats direction-ranking requests. Model fallback directions have a short cache rather than repeated calls during an outage.
- Book collections containing the original source are excluded as novelty recommendations. Distinct adaptations are retained.
- Home no longer promises exactly five results when verification can legitimately return fewer.

The geographic implementation follows [Qloo's documented locality boundary filter](https://github.com/qloo/docs-public/blob/main/reference/insights-api-deep-dive.md): the original locality ID is used where available, with `filter.location.radius=0`. Named destinations use the provider's locality resolver rather than invented coordinates.

## Per-query results

| Query | Flow | Cards | Example returned results |
| --- | --- | ---: | --- |
| Guillermo del Toro | Pass | 5 | The Hobbit: An Unexpected Journey (movie); Pan's Labyrinth (movie); The Hobbit: The Desolation of Smaug (movie) |
| Denis Villeneuve | Pass | 5 | Dune: Part Two (movie); Dune (movie); Arrival (movie) |
| Margaret Atwood | Pass | 5 | The Handmaid's Tale (book); The Testaments (book); Oryx and Crake (book) |
| Toni Morrison | Pass | 5 | Beloved (book); The Bluest Eye (book); Song of Solomon (book) |
| Björk | Pass | 5 | Dancer in the Dark (movie); Debut (album); Homogenic (album) |
| Kendrick Lamar | Pass | 5 | Black Panther (movie); To Pimp a Butterfly (album); Good Kid, M.A.A.D City (album) |
| Nintendo | Pass | 5 | Wii (product); Nintendo Entertainment System (product); Nintendo DS (product) |
| Patagonia | Pass | 1 | Yvon Chouinard (person) |
| Ben & Jerry's | Pass | 4 | Cherry Garcia (product); Phish Food (product); Ben Cohen (person) |
| Whiplash | Pass | 1 | Birdman or (The Unexpected Virtue of Ignorance) (movie) |
| Parasite | Pass | 3 | Joker (movie); The Platform (movie); Knives Out (movie) |
| The Left Hand of Darkness | Pass | 2 | The Dispossessed: An Ambiguous Utopia (book); Planet of Exile (book) |
| 1984 | Pass | 2 | Animal Farm (book); 1984 (Play) (book) |
| Stardew Valley | Pass | 2 | Slime Rancher (video game); My Time At Portia (video game) |
| Hades | Pass | 2 | Dead Cells (video game); Inscryption (video game) |
| Fleabag | Pass | 4 | Mouche (tv show); Better Things (tv show); Flowers (tv show) |
| 99% Invisible | Pass | 1 | What Can a Body Do?: How We Meet the Built World (book) |
| Reykjavik | Pass | 5 | La Primavera – Harpa (place); Sun Voyager (place); Hallgrimskirkja (place) |
| Portugal | Pass | 5 | LX Factory (place); Quinta da Regaleira (place); Praça do Comércio (place) |
| Apple | Pass | 5 | Apple TV+ (brand); iPhone (product); Mac (product) |

Counts reflect actual verified/qualified availability, not a forced target of five. Patagonia and several work searches correctly remain sparse.

## Other verification

- `npm run test:unit`: passed, including identity evidence, aliases, musical classification, hardware classification, adaptation copy, evidence-tail cache invalidation, book-source bundles, and request isolation.
- `npx tsc --noEmit --incremental false`: passed.
- `npm run lint`: passed.
- `npm run build`: passed.
- `tests/ui_mock.py`: all checks passed, including saves, removal/undo, sharing round-trip, Discover provenance, cross-map isolation, and reload.
- `tests/sparse_map.py`: passed at desktop, narrow mobile and landscape; includes ambiguous-name resolution, explicit continuation, failed request recovery, visible-parent graph edges and legacy saves.
- `tests/recovery_flow.py`: explicit fallback and map preservation passed at 1440px, 390px and 320px; short-screen and explicit transient retry checks are included.
- Live relevance benchmark: 24 labeled pairs, 2 runs per pair; zero false positives, precision 1.00, recall 0.85, accuracy 0.92, one unstable case, zero failed scoring calls. This is a small regression benchmark, not a population-wide accuracy guarantee.

## Remaining limits

The benchmark still conservatively misses some intended positive examples (Wolfwalkers from Studio Ghibli and Lawrence of Arabia from Dune). We did not reduce thresholds to force these through. Recommendations remain dependent on provider evidence and model judgments; missing data is reported rather than invented.

The 20-query browser suite is not a claim that every possible query, category expansion, or long-term personalized recommendation is perfect. The application changes fix the concrete audited failures and preserve explicit factual-versus-affinity distinctions.
