# Round 9 — ten new live queries, artwork, connections and recommendation edge cases

Date: 2026-10-28. Application revision: `f3bf0ff`.

This is an audit, not an application-fix claim. Browser flows use the real local app at `127.0.0.1:5173`; provider/model responses are not mocked. Tests and this report were added/updated; application code was not changed. Existing application/provider caches can serve repeated checks. The CSP compatibility experiment and synthetic identity counterexamples are explicitly separated from live application results below.

## Outcome

All ten new searches reached usable maps: nine primary flows and one explicit audience-match fallback. Initial results contain **38 discovery cards and 38 visible connections**, with the starting reference represented by a compact source anchor rather than a sixth discovery card. The first settled controls showed **35/38 cards with loaded artwork**. Three Yōko Ogawa fallback records have no image element because their response contains no verified image URL. A subsequent complete ten-query run showed **34/38**, with one additional actual cover failure: Wish returned HTTP 500 from Archive.org, also reproduced in a focused retry. Both outcomes are retained, not collapsed into an all-green image result.

Katy Perry was also rechecked separately: **five loaded covers, five visible connections**, no failed image requests or browser errors in that check. The previous missing-cover/zero-edge reproduction no longer occurs on this revision in the tested browser.

The ten-query sample is reproducible, stratified random selection from documented pools, seed `2026102809`; it is not a statistical accuracy sample.

| Query | Result type/relationship | Cards | Loaded artwork | Visible connections |
| --- | --- | ---: | ---: | ---: |
| Massive Attack | Music credits and albums | 5 | 5 | 5 |
| The Cure | Performed albums | 5 | 5 initially; 4 on repeat | 5 |
| Abbas Kiarostami | Directed films | 5 | 5 | 5 |
| Yōko Ogawa | Written books and source-work adaptations | 5 | 2 | 5 |
| Aesop | Explicit audience fallback; not claimed to be products | 5 | 5 | 5 |
| Tampopo | Eat Drink Man Woman | 1 | 1 | 1 |
| Convenience Store Woman | Three related books | 3 | 3 | 3 |
| Animal Well | Prince of Persia: The Lost Crown | 1 | 1 | 1 |
| Reservation Dogs | Three related TV series | 3 | 3 | 3 |
| Tbilisi | Places within the selected boundary | 5 | 5 | 5 |

Fewer than five results is not itself a failure: a relevance gate can legitimately retain one or three. Counts must describe actual insertions; unrelated fillers would be a regression.

## Confirmed issues and bounded findings

### 1. High deployment-compatibility risk — configured CSP blocks verified album artwork

`next.config.ts` permits images from Qloo and YouTube but not `coverartarchive.org` or its Archive.org redirect hosts. The new identity-bound album art uses those hosts. The same policy also omits the Open Library cover host used by the book-art path.

Controlled browser reproduction using the actual configured policy:

- Witness cover URL: blocked with request failure `csp`, complete image with natural width **0**.
- Existing Qloo image control: loads with natural width **160**.

The live development response has **no Content-Security-Policy header**, which explains why real album covers currently load there. This is a demonstrated incompatibility with the configured policy, **not a claim that a production deployment was tested or is currently broken**. A deployed-policy check is still required.

Required correction: allow only the trusted artwork hosts actually used, including validated redirect destinations, or serve verified artwork through a tightly allowlisted same-origin proxy. Do not permit arbitrary remote URLs or disable CSP broadly.

Reproducer: `tests/live_round9_csp.py`. The isolated meta-policy test logs that `frame-ancestors` is ignored in meta delivery; that does not affect the independently enforced `img-src` result.

### 1b. Medium — a redirect is accepted as verified artwork even when the final image fails

The complete rerun rendered Wish with `complete: true`, natural width **0**, and its image hidden by the error handler. A focused independent browser retry followed the Cover Art Archive release-group URL to the real Archive.org file host, which returned **HTTP 500**. Four other covers loaded. The earlier five-cover success shows this is a delivery/reliability failure, not proof that the album lacks an identified cover.

`verifiedArtwork()` accepts any redirect with a Location header without following it, then caches that artwork URL for 24 hours. That check does not establish that the terminal response is a usable image. The map hides the failed image but does not expose a retry action.

Required correction: bounded, allowlisted redirect/final-response validation and sensible transient-failure handling, with an intentional fallback/retry. Even a successful image check cannot guarantee future upstream uptime. Do not replace the cover with unrelated art, retry indefinitely, or blame JEV/Qloo for an Archive.org 500.

Reproducer: `PYTHONDONTWRITEBYTECODE=1 python3 tests/live_round9_art_loading.py --cure`; actual redirects, statuses and the failed image are in the evidence.

### 2. Medium — release-year evidence is lost before rejection identity is persisted

The server now considers differing years when excluding rejected title aliases, which is an improvement. However, `normalize()` does not copy provider `release_year` / `publication_year` into the discovery. The client then uses the first four-digit year in title/description as `yearHint`, or stores no year.

Offline reproduction through the actual normalization, year-hint and rejection helpers:

1. A synthetic movie has explicit provider `release_year: 1996`, an unqualified title, and a synopsis without a date.
2. Its normalized discovery loses that year; the rejection payload has no year.
3. A different provider identity with the same title/category and known year **2004** is consequently excluded too.

This is a production-helper counterexample with synthetic namesakes, **not a claimed live user rejection of a particular real film**. The previous round's title-key-only test is insufficient to evaluate the newer year-aware predicate; the new test exercises the actual pipeline.

Required correction: carry explicit structured year/external identity through discovery, feedback and memory. Prefer verified work IDs; do not infer publication identity from an arbitrary historical year in a synopsis. Missing identity should not silently become proof that every same-title work is the rejected work.

Reproducer: `tests/round9-static-edges.ts`.

### 3. Low — external covers advertise fabricated responsive widths

`qlooImage()` correctly leaves non-Qloo URLs unchanged, but `qlooSrcSet()` still emits that same fixed `front-250` URL as **160w, 240w and 420w**. This was observed in the loaded Katy Perry album image elements and reproduced through the production helper.

The files did load; this is **not** the cause of the original missing images. It gives the browser inaccurate intrinsic-width metadata and can reduce high-density artwork quality. Build real source-specific variants or omit width descriptors/srcset for fixed external artwork.

### 4. Remaining artwork coverage — three Yōko Ogawa works have no verified cover

The Housekeeper and the Professor, L'Annulaire, and The Memory Police are Wikidata-backed fallback records without image elements. A settled recheck still has two loaded images across five cards, no pending images and no failed image requests. Waiting longer cannot load a URL the response never provided.

Treat this as an artwork-coverage/fallback-design limitation, not evidence that the works are irrelevant. Preserve verified identities and use a deliberate missing-art treatment; never borrow a similarly titled work's cover. No claim is made that every absent cover can be recovered safely from currently available identifiers.

## JEV relevance check

Three newly returned pairs were hydrated with real Qloo descriptions/themes and the production tag-selection helper, then scored twice with actual JEV. Each batch also included an explicitly crossed negative control. Affinity was fixed at `0.95` to isolate semantic qualification; crossed negatives are test controls, not alleged Qloo recommendations.

| Proposed positive | Subject scores | Qualification |
| --- | --- | --- |
| Tampopo → Eat Drink Man Woman | 0.74 / 0.74 | Accepted twice |
| Convenience Store Woman → Breasts and Eggs | 0.59 / 0.57 | Rejected twice |
| Animal Well → Prince of Persia: The Lost Crown | 0.60 / 0.63 | Accepted twice |

All six negative-control decisions were rejected; all twelve decisions received scores. **10/12 decisions matched the proposed labels.** This is not a population accuracy estimate. The Japanese-fiction positive label is plausible, not objective factual ground truth; its initial inclusion versus standalone rejection is a calibration/recall warning across different batch contexts, not proof that identical prompts changed answers.

Do not lower every threshold to force five cards. Maintain separately labeled factual-credit, subject/craft and audience-affinity evaluation sets. A strict no-slop gate needs both precision controls and plausible-positive recall checks.

Re-run with credentials already configured:

```sh
ROUND7_FIXTURES=tests/round9-relevance-fixtures.json node --env-file=.env.local --experimental-strip-types --no-warnings tests/live_round7_relevance.ts
```

The legacy runner name does not change the new fixture identities. Its timestamped test anchor IDs force fresh relevance-cache entries; those synthetic suffixes are harness controls, not provider identities.

## Saving, memory, Discover and agent regressions rechecked

- Initial run of each new map: card opens, Save does not insert nodes, saved count survives reload, reload restores the map without repeating search, Gallery opens, no horizontal overflow in the tested viewport. An inspector availability probe may overlap Save; it is not an insertion request.
- Immediate save → unsave → Explore sends **zero positive anchors**, matching Saved 0.
- Cancellation leaves the initial **five cards unchanged** and reports stopped-before-reveal.
- Completed agent run with **one saved signal** inserts **four** new cards: map 5 → 9; final message says **four**, not five. One saved item is an input signal, not a request for exactly one output. This reproduction does not establish all possible deduplication-count edge cases.
- Resumed-map memory immediately and after settling contains the selected map's saved novel, not the other map's anchors.
- Discover save/reject does not add graph nodes; Add to map is the separate insertion action: graph 3 → 3 → 3 → 4, Saved 1.
- Discover launcher/close controls remain reachable at widths **390, 768, 900, 901 and 1440** in the targeted regression script.
- Verified album inspector still returns `no_qloo_identity` when a safe catalog crosswalk cannot be established. It now shows the explanation instead of disappearing category buttons and a misleading empty “more” group. This is an honest coverage boundary, not permission to substitute the artist silently.

## Harness correction and validation

The first image snapshots were taken around one second after reveal and flagged six maps. Several images were simply pending. Real HTTP/image settling later showed all covers loaded for those cases except the three genuinely image-free Yōko Ogawa records.

`capture_visuals` now distinguishes loaded, pending, failed and absent image elements, with an optional bounded settle wait. Round 9 uses that wait; existing immediate-snapshot callers retain their behavior. The first remaining-artwork diagnostic stopped on Aesop because it did not follow the explicit recovery action; the corrected diagnostic did so and completed all four cases. No provider failure is inferred from that harness mistake.

The bounded-settle ten-query repeat initially reported eight functional passes and two failures on the assertion that *no discovery request of any kind may begin after Save*. Animal Well and Aesop still had the same node count and Saved 1; their delayed availability prefetch overlapped that window. A separate real save/no-save control on Animal Well observed exactly one `probeTypes` request in each case, **881 ms / 883 ms after inspector opening**, and one graph card in both cases. The positive signal correctly differed only in the saved variant. The inspector schedules that probe after 900 ms regardless of Save. The harness now distinguishes this observed scheduled probe from an actual non-probe map-discovery request, and retains request classification in its result. It does not simply ignore arbitrary requests or permit Save to add nodes. Final targeted full save/reload/Gallery rechecks passed on both Animal Well and Aesop (explicit fallback for Aesop).

- `npm run test:unit`: pass.
- `npm run lint`: pass.
- Python syntax checks: pass.
- `git diff --check`: pass at validation.
- `tests/round9-static-edges.ts`: **three failing assertions exposing two code issues** (year transport/rejection and responsive cover metadata), deliberately retained as failing audit evidence.
- JEV calibration: **two proposed-positive disagreements**, no missing judgments.

Evidence: `/tmp/sideways-round9-review-evidence.json` and `/tmp/sideways-round9-followup-evidence.json`. The original Katy artwork DOM/HTTP result is retained in the first file; the full repeat, Archive.org 500, save/no-save timing controls and final save rechecks are retained in the second. Cure/Kiarostami initial settled screenshots: `/tmp/sideways-round9-art-{1,2}.png`; failed Cure retry: `/tmp/sideways-round9-art-cure-0.png`; remaining source checks: `/tmp/sideways-round9-art-remaining-{0,1,2,3}.png`.

These results are bounded to the recorded revision, providers, inputs and browser runs. They do not justify “all fixed,” guarantee five recommendations, or certify every factual credit and source record independently.
