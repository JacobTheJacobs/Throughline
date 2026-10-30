# Live discovery audit — 28 October 2026

This is the original, pre-fix audit. See [implemented fixes and live revalidation](live-query-fixes-2026-10-28.md) for the subsequent results.

## Verdict

Not reliable enough to call finished. Of 20 randomly sampled queries, **12 reached a map and 8 did not** through the tested first-choice search flow. Of the 12 maps, one required explicitly choosing an audience-affinity fallback. Two music searches returned incorrectly typed albums. Browser-flow success is not the same as correct recommendations.

All 12 loaded maps passed: open a card, save without fetching/adding discoveries, saved-count persistence after reload, Gallery navigation, and horizontal-overflow checks. No JavaScript crashes or request-queue 500s were observed in these 20 flows. Some searches correctly refused to invent connections, but their recovery UI was poor.

## Method and limitations

- Real Chromium sessions against `http://127.0.0.1:5173`, using real Qloo/JEV responses; no mocks.
- Fresh browser context and taste memory for every query; two concurrent sessions; desktop 1440×900 and mobile 390×844.
- Reproducible stratified random sampling, seed `20261028`, covering creators, authors, artists, brands, films, books, games, television, podcasts, and geography.
- When several exact-name/type records were shown, selected the first one. This deliberately tests first-choice ranking, not a claim that namesakes are the same person. Correct identified records were separately checked for the two affected creators.
- The initial harness did not recognize `videogame` and `locality` aliases. Hades and Portugal were rerun with those corrected. Both then reached real app-level empty/error responses; the original harness errors are not counted as app defects.
- Some initial failures waited for the harness's 105-second deadline after the app had already returned an error. **Those durations are not server-response times or evidence of an application hang.** The harness now recognizes those terminal messages promptly.
- Loaded-flow checks included saving and reload, not a full per-query category expansion, rejection, Explore-for-me, or long-term personalization audit. No relevance percentage is claimed.

## All 20 queries

| Query | Observed result | Assessment |
| --- | --- | --- |
| Guillermo del Toro | First suggested person record resolves to an unidentified author; no verified credits. Explicit audience fallback returns five items. | Entity-selection failure. The identified filmmaker record separately returns five credited films. |
| Denis Villeneuve | Dune: Part Two, Dune, Arrival, Blade Runner 2049, Prisoners. | Expected directed works; browser flow passed. |
| Margaret Atwood | First suggested person is labeled `Peerage person ID=323053`; no credits or audience data. | Namesake ranking failure. The identified author record separately returns five books, including The Handmaid's Tale and Oryx and Crake. |
| Toni Morrison | Beloved, The Bluest Eye, Song of Solomon, Jazz, Love. | Expected written works; browser flow passed. |
| Björk | Dancer in the Dark plus Debut, Homogenic, Vulnicura, Vespertine. | Relevant works, but all four albums are incorrectly typed `song`. |
| Kendrick Lamar | Black Panther, To Pimp a Butterfly, Good Kid, M.A.A.D City, Bad Blood, DAMN. | Relevant credits, but albums are incorrectly typed `song`. |
| Nintendo | Wii, Nintendo Entertainment System, Nintendo DS, Nintendo GameCube, Nintendo 64. | Recognizable verified products; browser flow passed. |
| Patagonia | Yvon Chouinard, correctly labeled founder. | One verified connection, not five products. Sparse-map UI worked. |
| Ben & Jerry's | Cherry Garcia, Phish Food, Ben Cohen, Jerry Greenfield. | Recognizable products and founders; browser flow passed. |
| Whiplash (2014) | HTTP 422; no map. Message: `End of this trail: nothing new beyond Whiplash. Explore another card.` | Search dead end with inappropriate new-search recovery copy. Movie-only category probe also returned `empty`. |
| Parasite (2019) | The Platform. | One plausible thematic match; browser flow passed. |
| The Left Hand of Darkness | HTTP 422; no map. Same end-of-trail message. | Both offered editions were checked; neither yielded a map. Raw Qloo did have book candidates. |
| 1984 (book) | Brave New World, Animal Farm / 1984, 1984 (Play). | Browser flow passed; bundle containing the original work is a weak novelty result. |
| Stardew Valley | HTTP 422; no map, end-of-trail message. | No usable discovery flow from a resolved popular game. |
| Hades (game) | Correct game selected after harness-alias correction; HTTP 422, end-of-trail message. | Genuine empty discovery result, not a missing game search record. |
| Fleabag | Mouche, returned as an adaptation. | Map/save/Gallery worked. Focused live inspector check showed `Adapted from Fleabag Fleabag.` |
| 99% Invisible | What Can a Body Do?: How We Meet the Built World. | One design/built-environment book match; browser flow passed. |
| Reykjavik | HTTP 422; seed lacks description/tags required for verification. | Evidence gap blocks geography discovery; no invented results. |
| Portugal | Correct locality selected after harness-alias correction; HTTP 503, no audience data. | Geography flow blocked. Choices also include an `artist` whose description says it is a country, not an artist. |
| Apple | Choices contain artist, album, game, and place, but not Apple Inc. | Intended brand hidden. Same search with `preferType: brand` immediately resolves Apple Inc. |

## Confirmed issues

### High: entity ranking cannot distinguish important same-name records

`rankChoices` sends JEV the query, candidate name, and type, but not the displayed description, year, image availability, or verified identity. Same-name/type candidates therefore have indistinguishable scoring questions. Margaret Atwood's namesake and Guillermo del Toro's unverified record appeared ahead of identified creator records. The latter also appeared twice under person/author types with the same entity ID.

Focused real requests to the identified records returned the expected credits. This establishes that the credits exist; the initial selection path is the problem.

Source: `app/api/discover/route.ts`, `rankChoices` and ambiguity assembly.

### High: album types are guessed from the relationship

`directConnectionType` falls back to `song` for `Performed by` and `Music by`, although a performer relationship does not establish whether an item is a song, album, or film. The live Björk and Kendrick responses demonstrate the error.

Independent source checks: [Debut is an album](https://www.wikidata.org/wiki/Q753601); [To Pimp a Butterfly is an album](https://www.wikidata.org/wiki/Q19602856). Their returned card IDs point to those same source records.

Source: `lib/direct-connections.ts` and the verified-credit fallback in `app/api/discover/route.ts`.

### High: intended brand omitted from ambiguity choices

Normal `Apple` search omitted Apple Inc. A focused request with the same text and `preferType: brand` returned brand ID `D5B78065-6DBB-4DDB-80DF-6495B9B1006B`. Thus the company was available in search; it was not absent from Qloo.

The ambiguity path returns exact-name choices before including the intended name variant `Apple Inc`.

### High: retrieval-to-relevance path rejects entire candidate sets

Direct raw Qloo checks returned HTTP 200 and populated candidates for:

- Whiplash: Birdman, The Grand Budapest Hotel, Boyhood, The Imitation Game, Interstellar, Gone Girl.
- Hades: Death's Door, Outer Wilds, Loop Hero, Inscryption, Cult of the Lamb, Dead Cells.
- The Left Hand of Darkness: The Dispossessed, The Lathe of Heaven, Rocannon's World, Planet of Exile, Neuromancer, plus an evidently weak unrelated children's-book match.

The app still produced no map. **This does not prove every raw candidate should pass.** It establishes that the empty results are not simply missing upstream candidate data. Candidate evidence, score decisions, and filtering need inspection before changing thresholds. Do not remove the relevance gate or invent replacements merely to fill five slots.

### Medium: new-search failures strand the user

The root search reuses `End of this trail ... Explore another card` even when there is no map or card to explore. Empty candidate sets, unsupported signals, missing evidence, and service failure also need distinct recovery states. Portugal's no-data state currently uses HTTP 503, which resembles a transient outage rather than unsupported data.

### Medium: geography aliases and metadata need normalization

Portugal is offered as `place` and `locality`, while the UI exposes Destinations. Reykjavik lacks enough evidence to pass the gate. Portugal is also offered as an artist despite its description explicitly contradicting that category. Surface the intended geographic meaning and do not treat contradictory metadata as a reliable recommendation anchor.

### Low: adaptation explanation repeats the source title

The live Fleabag inspector displayed `Adapted from Fleabag Fleabag.` The relationship already contains the source title, then `directConnectionReason` appends it again.

## What was changed during this audit

Only the reusable audit script and this report were added. No application fixes were made in this turn. Existing working-tree changes from the previous fix were preserved.

Run again: `python3 -u tests/live_queries.py`. `FLOW_PASS` only means browser and response-contract checks passed; independently review returned types and meanings as above.
