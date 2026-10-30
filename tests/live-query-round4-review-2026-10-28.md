# Fourth live discovery audit — 28 October 2026

Application commit: `46e99de`, unchanged from the third audit. This turn adds tests and evidence only; no application fixes were made.

## Result

Ten new, reproducibly sampled queries: **9 normal initial browser flows, 1 explicit audience fallback, 0 initial flow failures**. **Seven of the nine normal flows also received HTTP 429 from `/api/suggestions`**. These are qualified flow passes, not a relevance or full-functionality all-clear.

Real local application: `http://127.0.0.1:5173`. Real configured providers; no mocked API responses. Fresh isolated browser storage, desktop/mobile viewports, concurrency two. Sampling seed: `2026102804`. Queries were selected before requests; failures were not replaced.

## New findings

### 1. High — an incorrect external identity prevents a real artist's work from being retrieved

The selected Aphex Twin record has the expected name and Richard D. James description, but its external Wikidata ID is **Q97228784**. A live read of that entity returns **Gak — Japanese guitarist**, not Aphex Twin. The selected Qloo record is `4278382F-4991-4D63-B207-942D86A26ACB`.

The direct-work lookup trusts the external ID and reports no verified work. The recovery is honest and does not invent credits, but the empty result does not establish that the artist lacks work: the [official Aphex Twin store](https://aphextwin.warp.net/?lang=en_US) lists albums including Selected Ambient Works Volume II and Drukqs.

The browser test explicitly chose **Try audience matches** afterward. Black Mirror, One Flew Over the Cuckoo's Nest, TrueAnon, The OA and Lord of the Flies were then labeled audience overlap, not factual connections. Those results must not be reported as invented artist credits or as an unauthorized automatic fallback.

Code: [external-ID preference](../app/api/discover/route.ts#L59), [direct identity lookup](../app/api/discover/route.ts#L60).

Required correction: check that linked identities agree with the selected entity before factual retrieval; use alternate verified identifiers when they do not. A syntactically valid QID is not an identity check. Avoid a hardcoded Aphex-only patch.

### 2. High — valid short names enter an empty clarification loop

Live endpoint requests for **Up**, **Up movie**, **U2**, and **U2 band** all return `mode: clarify` with an empty `choices` array. Actual 390px browser runs for Up and U2 show the empty quick-question form, not selectable identities.

The parser strips the category suffix, then the resolver rejects the remaining name solely because it is shorter than three characters. Even explicit category clues therefore fail to recover these examples.

Code: [short-name rejection](../app/api/discover/route.ts#L180), [suffix interpretation](../app/api/discover/route.ts#L18).

Required correction: use retrieved identities and explicit category intent for short names; distinguish an empty/meaningless input from a valid two-character title or artist. Preserve literal-title matching before interpreting suffix words.

### 3. High — a novel author is presented as the film's screenwriter

Kazuo Ishiguro's first direct result is **The Remains of the Day (1993 film)**, labeled **Screenplay by Kazuo Ishiguro** and **Verified direct relationship**. Its own returned description says the film was adapted from his novel.

The [BFI film credits](https://www.bfi.org.uk/film/38c090b6-bf34-5809-9a4c-f350b62ce37c/the-remains-of-the-day) and [AFI catalog](https://catalog.afi.com/Catalog/moviedetails/59638) identify Ruth Prawer Jhabvala as the screenwriter; Ishiguro wrote the source novel. A source-work connection is valid, but the role is not interchangeable.

The live Wikidata film item Q1625242 has truthy P58 claims for Jhabvala, Harold Pinter and Ishiguro. The returned claims have no role qualifiers that would solve this merely by filtering qualifiers. They are imported statements, not independent confirmation of released-screen credits.

Code: [simplified direct-credit query](../app/api/discover/route.ts#L91).

Required correction: retain provenance and source-work roles, reconcile conflicting credits against authoritative released-film credits, and qualify uncertainty. Do not turn every database property into an unqualified verified credit. Living and other legitimate screenwriting work should not be removed merely because this one credit is wrong.

### 4. Medium — immediate Unsave sends stale positive graph memory to the agent

Reproduced through visible browser controls:

1. Open a fresh Her map and Blue Is the Warmest Colour.
2. Save it, wait 1.4 seconds, then unsave it.
3. Close details and immediately choose Explore for me.

The captured real `/api/agent` request simultaneously contains:

```text
Visible Saved count: 0
cards[Blue Is the Warmest Colour].liked: false
likes: []
memory.positiveAnchors: Blue Is the Warmest Colour, weight 5
memory.summary: Strong signals: Blue Is the Warmest Colour ...
```

The memory refresh is debounced by 500ms while the agent sends the cached memory immediately. Latest explicit feedback and retrieved memory are not a consistent snapshot.

Code: [debounced memory refresh](../app/page.tsx#L126), [feedback operation](../app/page.tsx#L199), [agent request](../app/page.tsx#L234).

The agent was explicitly cancelled before reveal. This proves contradictory input, **not** that this run ultimately displayed an incorrect recommendation. Cancellation passed: the map stayed at three cards and reported Stopped before reveal. Your map is unchanged.

Required correction: reconcile memory against current explicit feedback or await a version-matched snapshot before starting the run. An old strong-positive signal should not survive a newer explicit unlove. Preserve legitimate non-save exploration memory rather than deleting all history.

### 5. Medium — quota errors remove primary exploration actions without explaining why

Seven sampled queries received `/api/suggestions` HTTP 429. The response explicitly says the feature's daily limit was reached. In a separate actual inspector check, the primary category-button count is **zero**, while the panel still says **Checking which categories have verified matches…**. The secondary 10 more toggle remains, so this is not proof that every category is inaccessible.

The client discards the request failure without rendering an error or useful degraded state. The server's template fallback is downstream of its guard, so it cannot handle guard rejection.

Code: [client suggestions request](../app/page.tsx#L255), [guard before fallback](../app/api/suggestions/route.ts#L27), [shared-IP feature limits](../lib/guard.ts).

Required correction: show a truthful rate-limited state; retain safe local category navigation or cached directions without claiming availability was checked. Do not retry repeatedly, bypass the guard, or fabricate available matches.

Limit note: the running local server already had accumulated usage from testing/other local use. This is not a fresh-user load test or evidence that a normal fresh user necessarily hits the cap within ten searches. The cap was not reset or bypassed. Exhaustion limits what can be certified about availability and direction ranking in this run.

### 6. Low — malformed null card request produces an avoidable 500

Real POST bodies containing JSON `null`:

| Endpoint | Status | Observation |
| --- | ---: | --- |
| `/api/discover` | 400 | Invalid discovery request |
| `/api/agent` | 400 | Start a map first |
| `/api/card` | **500** | Empty response body |
| `/api/suggestions` | 429 | Daily guard prevents testing deeper validation |

Code: [unguarded body.card access](../app/api/card/route.ts#L24). `readJson` can return null. Validate an object before accessing its fields. Do not claim a live null-body 500 for suggestions: the quota prevented that observation.

### 7. Low — mathematically equal JEV threshold margins behave differently

The real `qualifiesAnchorMatch` requires `subject - loose >= .2`. With affinity .9:

| Subject | Loose | JavaScript margin | Accepted |
| ---: | ---: | --- | --- |
| .60 | .40 | .19999999999999996 | No |
| .61 | .41 | .2 | Yes |
| .70 | .50 | .19999999999999996 | No |
| .80 | .60 | .20000000000000007 | Yes |

Code: [margin gate](../lib/recommendation-ranker.ts#L34). This is a deterministic numeric-boundary check of production code, not a mocked provider result. No particular live candidate in this run was proven lost at this exact boundary. Adopt an explicit precision/tolerance policy without meaningfully lowering the relevance threshold.

### 8. Medium — base-game identity points to an upgraded edition, then recommends that edition as new

The selected **Disco Elysium (2019)** record links to Wikidata **Q127164835**, whose English label is **Disco Elysium: The Final Cut** and description identifies a 2021 video game. A new recommendation is then Disco Elysium: The Final Cut under a different Qloo ID.

This is an edition/identity ambiguity, not proof the recommendation is useless: an upgraded edition can be useful if identified as such. The Wikidata item itself has mixed release metadata, so date alone must not be used to decide canonical identity. Validate edition relationships and label enhanced editions rather than presenting them as an unexplained independent new game.

## Ten new queries

| Query | Initial path | Cards | Returned examples / caveat |
| --- | --- | ---: | --- |
| Ridley Scott | Direct | 5 | Gladiator, Alien, The Martian, Blade Runner, Prometheus; Directed by. |
| Kazuo Ishiguro | Direct | 5 | The Remains of the Day, Living, The Saddest Music in the World, The White Countess, Never Let Me Go. Wrong role on the first film. |
| Aphex Twin | Explicit audience fallback | 5 | No direct work retrieved; bad external identity. Audience matches only after an explicit recovery click. |
| Adidas | Direct | 5 | Jabulani, Brazuca, Telstar, Teamgeist, Telstar 18; Made by. Suggestions 429. |
| Her (2013) | Affinity | 3 | Blue Is the Warmest Colour, I Origins, Before Midnight. Suggestions 429. |
| Sapiens | Affinity | 3 | Upheaval, The Brain: The Story of You, Homo Deus. Suggestions 429. |
| Disco Elysium (2019) | Affinity | 3 | The Final Cut, The Forgotten City, Vampire: The Masquerade - Bloodlines. Edition mismatch; suggestions 429. |
| Dark (2017) | Affinity | 2 | 1899, Devs. Suggestions 429. |
| Serial | Affinity | 2 | S-Town, Undisclosed. Suggestions 429. |
| Berlin | Direct | 5 | East Side Gallery, Domcafé im Berliner Dom, Holocaust Memorial, Brandenburg Gate, Checkpoint Charlie; Located in. Suggestions 429. |

A browser-flow pass checks one to five unique non-source cards, source context, explanation labels, opening a card, Save without graph expansion or extra discovery requests, Saved 1 after reload without a repeated search, Gallery navigation, and no horizontal overflow. Expected year/identity clues were checked where clarification choices exposed them. This does not verify every credit, metadata field, future ranker decision or subject connection.

Returning two or three candidates is not inherently a bug. There must not be invented padding to reach five. This audit does not establish that every smaller set contains all relevant available results.

## Persisting regression checks

The following earlier findings were rechecked live and remain present on the unchanged application commit:

- The Jungle Book resolves to The Jungle, not the literal requested title.
- The Artist resolves to the artist The, not the literal film title.

Previous Iceland, cross-provider feedback/novelty, Murakami recall and Snow White credit findings are in the third report. Those entire paths were not rerun this turn and are not counted as fresh reproductions here.

## Validation and boundaries

- `npm run test:unit`: passed (one top-level test-file result).
- Save persistence, no save-triggered expansion and Gallery checks passed in the sampled flows.
- Explicit agent cancellation left the map unchanged.
- No new standalone labeled JEV semantic benchmark was run this turn. The previous turn's 16 model votes must not be presented as a fresh round-four accuracy statistic.
- Memory checks cover the actual map-scoped request and immediate-feedback race. They do not establish comprehensive RAG retrieval accuracy, canonical identity correctness, or coverage across every category.
- No production build was run: application code was not changed.

Reproduction scripts: `tests/live_queries_round4.py`, `tests/live_round4_edges.py`, shared `tests/live_queries.py` and `tests/live_round3_paths.py`. Extra endpoint checks and numeric-boundary checks are preserved in raw evidence rather than a new test runner.

Raw isolated-browser/API evidence: `/tmp/sideways-round4-review-evidence.json`. No credentials are included. The new test scripts observe real requests; they do not mock provider responses.

Priority: repair identity/title resolution and factual role attribution; make explicit feedback authoritative and current; gracefully degrade category navigation under quota; then harden malformed inputs, edition handling and numeric boundaries. Raising affinity or JEV thresholds cannot repair a wrong anchor or incorrect factual source role.
