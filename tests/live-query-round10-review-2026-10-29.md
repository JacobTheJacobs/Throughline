# Throughline production review — 29 October 2026

This review used the actual public EC2 deployment, real Qloo/Wikidata/JEV calls and isolated browser contexts. No provider responses were mocked. Random selection is stratified across ten pools with seed `2026102910`; these are reproducible cases, not a statistical accuracy sample. The original deployment and the patched deployment were both exercised.

## Live searches after fixes

| Query | Discoveries | Loaded artwork | Visible edges |
| --- | ---: | ---: | ---: |
| Portishead | 5 | 5 | 5 |
| Janelle Monáe | 5 | 4 | 5 |
| Céline Sciamma | 5 | 5 | 5 |
| Italo Calvino | 5 | 1 | 5 |
| Fjällräven | 1 | 0 | 1 |
| The Lighthouse | 5 | 5 | 5 |
| Never Let Me Go | 4 | 4 | 4 |
| Return of the Obra Dinn | 4 | 2 | 4 |
| Dark | 3 | 3 | 3 |
| Valparaíso (Indiana choice) | 5 | 5 | 5 |

All ten passed the browser flow: form submission, entity resolution/clarification, unique non-source cards, relationship explanations, visible connections, inspector opening, save without expansion, save surviving reload, and Gallery. Total: **42 cards, 42 edges, 34 loaded images, zero failed image elements** in the final sample. Eight records had no usable image URL; those display intentional fallbacks. Fewer than five discoveries can be a correct relevance/coverage outcome.

The unqualified Valparaíso case explicitly offered multiple locations. The harness picked the first matching destination (Indiana); this is not proof that it inferred a Chilean intent. A separate check required the description to name **Chile**, selected `F8276DBD-51BC-43B9-8BD3-BF7B4D5D1629`, and passed with five local results including Playa Caleta Portales, Sotomayor Square and Prat Pier. Country/region descriptions remain necessary for ambiguous place names.

Extra regressions: **Katy Perry, The Cure, and Abbas Kiarostami each rendered five loaded covers and five visible connections**, without image failures or browser console errors in the recorded checks.

## Confirmed fixes

1. Production CSP blocked Cover Art Archive/Open Library artwork. Updated both the app policy and Caddy policy for the used cover hosts and Archive.org redirects. Removed `unsafe-eval`; production hydration, search, save and Gallery still pass. Inline scripts remain allowed by the current framework policy; this is not a nonce-based strict CSP.
2. Artwork verification accepted any redirect as success. Added bounded redirect traversal, an HTTPS host allowlist, terminal image content-type checking, and distinct missing/transient results. Untrusted redirect targets are never fetched. A terminal upstream outage cannot be guaranteed away.
3. A 900ms Qloo image HEAD timeout deleted otherwise valid image URLs. Transient failures now leave the identity-bound URL available for the browser; definite absence still removes it.
4. External fixed-width covers advertised fabricated responsive sizes. Only Qloo's real resize URLs now receive width descriptors.
5. Provider release years were lost before rejection identity was persisted. Structured years now survive normalization, restoration and exact sharing. Rejection no longer infers a work's release year from arbitrary historical years in a synopsis. The previous round's three failing production-helper counterexamples now pass.
6. Roseland NYC Live was labeled album despite an explicit documentary-film description and an ambiguous album class. Concrete concert/documentary-film descriptions now take priority, including repair of older saves.
7. Forged `cf-ray`/`cf-connecting-ip` headers bypassed rate-limit buckets. The app now trusts only the explicitly enabled private proxy path and the last appended forwarded peer address. Caddy strips spoofable alternative identity headers. Previously all normal users also shared the `local` bucket because trusted-proxy mode was unset; the deployed app now enables it.
8. `null` bodies caused 500s in discovery's fallback wrapper and suggestions. Object validation now returns 400; the wrapper reads a bounded JSON body before parsing fallback properties. Agent feedback also requires string entity types. Caddy additionally caps request bodies at 300KB.
9. The actual deployed runtime had five advisories despite the source production audit reporting zero. Patched React/React DOM/React server components to 19.2.8 and constrained image-size 2.0.4, satori 0.33.5 and fflate 0.7.5. The final deployed runtime audit reports **zero known advisories** across its 140-package inventory. This is an advisory result, not a proof of absence of vulnerabilities.
10. The app ran as root with writable container storage. It now runs as UID 1000 with a read-only root filesystem, bounded temporary storage, all capabilities dropped, no-new-privileges, a PID limit, memory limits, and rotated Docker logs. No app port is publicly published. Deployment checks the candidate before replacement and retains a stopped previous container for rollback.
11. Mobile users could not reach recent explorations because the sidebar disappears. Added a mobile Recents button using the existing saved-explorations panel.
12. Visual inspection revealed the onboarding tip survived returning Home and covered the input. It is now restricted to Map, reset on Home navigation, and given an appropriate mobile width. Home navigation also clears stale toast messages.

## Saving, exploring and memory

Two maps were saved in the same browser. Save → unsave → save preserved counts; saving did not add cards. Reload retained each save. Gallery hid Explore with Qloo. Resuming The Lighthouse sent exactly one positive signal belonging to that map, with no Dark-map positive anchor in retrieved memory. A completed agent run grew the map **5 → 10**, streamed five additions and reported five. The same flow passed again on the hardened production build.

RAG here is browser-local IndexedDB feedback and graph retrieval, not an external vector database. The current explicit feedback filters stale memory before requests. These tests cover this sequence, not every concurrent-tab/event-order case.

## JEV quality

The actual JEV benchmark ran 24 labeled pairs three times: **72 decisions, no missing calls, no unstable cases, no labeled false positives, precision 1.00 and recall 0.92** by majority vote. Dune → Lawrence of Arabia was the sole labeled positive rejected; its subject scores were 0.53–0.54. The strict gate was retained. The benchmark descriptions/labels are curated, including previously retrieved examples; these figures must not be advertised as overall product accuracy or independent verification of every returned credit.

The first benchmark invocation omitted provider environment variables and failed with missing scores. The credentialed run is the result above. The first post-CSP browser rerun failed because the harness used page-side eval in `wait_for_function`; a protocol-based polling helper corrected the test without re-enabling unsafe-eval.

## Security and UI checks

- Requests for `.env`, `.env.local`, `.git/config`, `server.js`, `package.json` and `app.env`: 404. Unsupported API GETs: 405. Foreign-origin POST: 403. Null bodies on all four POST APIs: 400 after deployment.
- Exact runtime secret-value scan of **39 public asset files: no matches**. Values were not printed by this audit. API credentials remain server-side.
- An imported shared map with HTML/event-handler text, a javascript link and an HTTP metadata-address image did not execute script; the unsafe link/image were dropped.
- Dedicated EC2 security group allows only 80/443; SSH is not publicly allowed. IMDSv2 is required; secret-file permissions are 600. Other EC2 instances were not modified.
- Home input reachability and horizontal overflow checked at 320×568, 390×844, 768×1024, 1440×900 and 844×390. Map overflow checked at 320, 390, 768 and 1440 widths. Screenshots inspected; these checks are not a full accessibility conformance audit.
- Lint, unit tests, production build, deployment readiness and production HTTP checks pass.

## Remaining limitations/action

- **Rotate provider credentials previously printed in private SSM deployment output in the earlier session.** No public exposure was found here; rotation cannot be established by an asset scan and was not performed by this review.
- Eight sample records have no usable image URL. Missing art is shown honestly; unrelated covers are not substituted. Remote cover services can still fail later.
- Same-name geography still requires user clarification. JEV/Qloo and Wikidata coverage are not universal. Direct relationships are source-record claims, not a manual release-credit audit.
- Local browser storage is origin-specific. The old Sideways-to-Throughline hostname redirect does not migrate the old hostname's IndexedDB/localStorage; old data is not automatically made available at the new origin.
- This was a bounded source/server/browser review, not a penetration-test certification. Rate limits are process-local and reset on service replacement; the public demo is not an authenticated multi-user service.

Evidence: `tests/round10-evidence-2026-10-29.json`; reproducible runners `live_queries_round10.py`, `live_security_round10.py`, `live_state_round10.py`, `live_shared_safety_round10.py`. Full before/after provider/browser results and image HTTP logs are retained under `/tmp/throughline-round10-*` for this session.

Advisories consulted: https://github.com/advisories/GHSA-wx67-qw84-cm4g ; https://github.com/advisories/GHSA-5p2g-fcmc-qvqq ; https://github.com/advisories/GHSA-wx4j-mvgx-mqwp .
