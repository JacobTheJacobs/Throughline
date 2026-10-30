# Throughline live review — round 17, 29 October 2026

## Verdict

Ten new seeded real-provider browser flows completed. **One live semantic failure remains: Québec City silently resolves to a broader Québec record and returns Montréal venues.** A new synthetic geography-helper counterexample also survives the latest region fix. The prior Ontario and nested Scotland counterexamples are fixed in the tested controls.

No application implementation or production changes in this review; only review scripts/report added. Existing untracked demo/maintenance files preserved.

## Findings

### High — a literal city name becomes a broader region without clarification

Live form input **Québec City** returned seed `AA6A179E-A8CC-4268-9E58-9ED963050A29`, named `Québec`, with no clarification. Results included Parc Jean-Drapeau, Place des Arts and MTELUS; their own returned descriptions identify them as Montréal venues. These do not satisfy a Québec City request. Parliament Hill and Château Frontenac were also returned; no independent claim about the precise boundary of the selected provider record is necessary to establish the city-intent mismatch.

An additional direct public API request with `text: Québec City` reproduced mode=live, the same seed and the same mixed results. This is not the earlier mistake of a harness selecting the wrong visible candidate; there was no meaning chooser.

The relevant source path is `splitTypedQuery` and the preferred-candidate resolution in `app/api/discover/route.ts`: when the full query has no exact-name match, the trailing `City` token is interpreted as a generic destination category. The remaining name is then eligible to resolve to a region; city and region share the same canonical category. Preserve literal geographic names/aliases and requested administrative granularity, or explicitly clarify city versus province. Do not repair this with a Québec-only exception.

### Medium — a real administrative region is exempted because its name contains its country

`lib/geography.ts` now correctly rejects Ontario→British Columbia without depending on the other retrieved results. However, `administrativeRegion` treats any region containing the country's first word as country-wide.

`tests/geography_regions_round17.mjs`, using the actual exported helpers with explicit synthetic evidence:

| Selected | Candidate | Actual acceptance | Expected |
| --- | --- | --- | --- |
| Ontario, Canada | Vancouver, British Columbia, Canada | false | false |
| Île-de-France, France | Bordeaux, Nouvelle-Aquitaine, France | true | false |

Île-de-France is not a country-wide synonym. Use explicit validated equivalences or administrative identity, not a country-word substring heuristic. This is a local predicate counterexample, **not** a separately observed live Bordeaux recommendation.

### Medium — two real cover URLs fail during the browser flow

Wet Leg and Moisturizer cover image elements completed with naturalWidth0 in the live run. These are different from absent art. Follow-up GETs to both exact Cover Art Archive URLs returned200 image/jpeg via Archive.org hosts, so the later source URLs were available. The initial failure may be transient; the exact browser/network cause was not established. Preserve the identity-safe fallback, but provide a bounded retry/retry action rather than permanently treating a transient failure as missing cover art for the session. Do not substitute unrelated images.

Seven other cards had no image element: four Annie Ernaux references, the Acne Studios founder, two Kentucky Route Zero recommendations. These are honest missing-art fallbacks, not broken requests.

### Medium — the flow oracle does not validate automatically selected geographic meanings

The query runner filtered country expectations only when a clarification modal appeared. An automatic live response bypassed that check, so Québec City was labeled FLOW_PASS. Review content independently and assert requested identity/granularity after both automatic and user-confirmed resolution. Ten flow passes must not be advertised as ten accuracy passes.

### Remaining presentation limitations

- Generic candidate mood/tag descriptions do not always expose the specific shared connection JEV accepted.
- Kentucky Route Zero returned two honestly labeled looser matches; they must not be counted as strict subject-gate passes.
- The new looser wording no longer implies strict matches are present when the whole batch is looser. Verified in the returned live text.
- Long social actions remain explicitly start-only; Copy exact link preserves descriptions/map. This is a disclosed limitation.
- The fast nested-confirmation fixture again measured focus outside during opening. The wait-aware follow-up passed3cycles×8Tabs plus Escape/opener restoration. No new stable focus-escape regression established.

## Ten fresh random searches

Seed `2026102917`, stratified pools, two concurrent isolated contexts, no provider mocks. Live provider-backed responses may reuse application/provider caches; this is not proof of a new JEV evaluation for every repeated path. Form entry, unique non-source IDs, explanations, visible edges, card opening, Save behavior, reload and Gallery checked.

| Query | Flow | Cards | Loaded art | Visible edges |
| --- | --- | ---: | ---: | ---: |
| Tamino | Pass | 1 | 1 | 1 |
| Wet Leg | Pass;2failed cover elements | 4 | 2 | 4 |
| Alice Rohrwacher | Pass | 5 | 5 | 5 |
| Annie Ernaux | Pass | 5 | 1 | 5 |
| Acne Studios | Pass | 1 | 0 | 1 |
| The Worst Person in the World | Pass | 3 | 3 | 3 |
| Convenience Store Woman | Pass | 3 | 3 | 3 |
| Kentucky Route Zero | Pass;looser tier | 2 | 0 | 2 |
| Detectorists | Pass | 2 | 2 | 2 |
| Québec City | Flow pass;semantic failure above | 5 | 5 | 5 |
| **Total** | **10flow passes, not10accuracy passes** | **31** | **22** | **31** |

Seven absent-image fallbacks,two failed image elements,zero pending. Fewer than five discoveries is not itself a bug. This sample is not a statistically measured relevance benchmark; every source credit was not independently fact-checked.

## Previous regressions and feedback

- Scotland entity `A75E2277-6EDF-4E18-831C-096E806E51AE` returns Edinburgh Castle/Botanic Garden/etc. at depths1and2, with no Indiana links.
- `Freitag brand` now returns `reason:type_missing`, explicitly explains no matching brand, and offers only the similarly named flagship store—not Friday the13th movies. This verifies recovery, not absence of the brand from the entire provider database.
- The Lighthouse/Dark each passed save→unsave→save,reload,no Save-triggered expansion,and Gallery hiding exploration.
- Resuming The Lighthouse sent one map-local positive signal and no positive anchor from the other map.
- Actual agent run3→8,streamed/reported five additions.
- Rejected I'm Thinking of Ending Things remained absent after reload and after exploration;dislikes/excludeIds contained it;positive memory did not. Map3→2 after rejection,then→7 after agent.
- Bounded sequences only;no guarantee about simultaneous-tab conflicts,all editions/aliases or every candidate's semantic quality. No new independent JEV precision/recall benchmark.

## Security,server and UI

- Fourteen public-route exposure/body/origin checks passed:sensitive paths404,unsupported GET405,null bodies400,foreign Origin403,oversized JSON400.
- Shared HTML/event-handler text did not execute;unsafe javascript links and HTTP metadata-address images were dropped. Not a comprehensive XSS/SSRF assessment.
- Exact deployed provider-key scan:two configured values,39public files,zero skipped,zero matching files. No credentials printed. Private logs/history and key rotation are not established by this scan.
- Actual installed inventory137package names:zero returned advisories from npm registry bulk endpoint. This is known-advisory coverage,not a security guarantee.
- Image `2026-10-29-6ba679a`,health healthy,user=node,rootfs read-only,app port unpublished. Secretfile600/root,Caddy logs10MB×3. Disk72%used,2.3GiBfree;monitor headroom during repeated deployments. Other EC2s untouched.
- Filesystem-budget contention400allowed/200capped,zero busy,final400. No provider calls;crash/stale-lock cases not exhausted.
- Lint and47individual unit tests passed. Region-name counterexample is additional to those tests.
- Share initial focus/Tab containment,description-preserving exact link,Wikidata badge,gallery restoration,44×44px Recents close passed. Wait-aware nested confirmation3×8Tabs passed.
- Home input reachability/no-overflow320×568,390×844,768×1024,1440×900,844×390;map widths320/390/768/1440 passed. Not a full accessibility conformance audit.

## Reproduction and evidence

- `tests/live_queries_round17.py`; `/tmp/throughline-round17-results.json`.
- `tests/geography_regions_round17.mjs` (synthetic actual-helper controls).
- `/tmp/throughline-round17-identity-controls.json` (real Québec City/Freitag API controls).
- Existing geography,state,rejection,UI,confirmation,security,sanitization runners rerun;their corresponding `/tmp` evidence refreshed.
- Exact cover URLs and initial failed-element metadata retained in the full query evidence;follow-up terminal GETs both200image/jpeg.
- Sanitized server/asset/advisory SSM command `d206775d-fa05-48a4-84d0-02acb755fe1a`.

No new public credential leak found in the tested scope. Key rotation remains unverified. No application implementation or production changes made during this review.
