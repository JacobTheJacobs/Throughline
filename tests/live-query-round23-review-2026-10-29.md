# Round 23 — live discovery, UI/UX, security and server review

2026-10-29. Production https://throughline.51-21-210-47.sslip.io. Local and deployed commit remain 9c18255. Review only: no application fixes, deployments or infrastructure changes. Read-only server inspection used the AWS compute skill and only the dedicated Throughline instance.

## New findings

### High product impact: Copenhagen's intended Denmark path fails

The main run's country-qualified destination assertion failed, not merely the flow harness. Actual offered destination choices:

- 9951D1CC-F159-4638-B780-CCB39AEC4957, Copenhagen, “Area in New York, United States of America”, linked identity Q3459904; first in chooser.
- 82DCD455-A5AB-42D0-B390-11218B0C7FF0, Copenhagen, “Geographic area”, no linked identity/country description.

A separate first-choice control opened the New York record and returned The Cottage Inn and Dollar General. That is a successful flow for the selected US record, NOT a successful Denmark search. A second explicit control selected the unlabeled destination: zero cards, recovery says no new places returned within Copenhagen. Thus neither control establishes a working Denmark city journey. Do not merge these flow controls into a 10/10 accuracy claim.

Source review: choiceQuality in lib/search-choices.ts heavily rewards linked identity/descriptive metadata, so a well-described smaller namesake can outrank a higher-popularity record without identity evidence. Ordering alone is not proof an entity is wrong, but country/city identity needs to be visible and reliable. Fix identity enrichment/choice labels and verify geographic bounds; don't hard-code Copenhagen or silently substitute another city.

Evidence: /tmp/throughline-round23-results.json, /tmp/throughline-round23-copenhagen.log, /tmp/throughline-round23-copenhagen-second.json and .log. Controls use real production responses, not mocks.

### Medium: card search-link cache ignores improved identity evidence

Two bounded live /api/card calls used a disposable authored ID for Dune/book. First had name/type only; second added “1965 novel by Frank Herbert” and a science-fiction tag. Both200; first source=jev, second omitted source; query/options stayed identical and did not gain the supplied creator/year evidence. Source at app/api/card/route.ts:25 confirms the cache key is only id/name/type, despite generation and scoring depending on description/tags. The cached response also drops its source field.

This is a cache invalidation defect, not proof a specific external search would return the wrong result. Use sanitized evidence plus generator version in the cache key and preserve provenance on cache hits. Review the trust boundary too: supplied metadata is caller-controlled and the cache is process-shared; no cross-user poisoning experiment was performed.

Evidence: tests/live_card_cache_round23.py; /tmp/throughline-round23-card-cache.json. Authored metadata, real scorer, no provider mocking.

### Medium: search templates discard meaningful sequel/subtitle identity

Pure-function checks of lib/card.ts shortName show:

- Spider-Man: Into the Spider-Verse → Spider-Man
- The Lord of the Rings: The Two Towers → The Lord of the Rings
- Star Wars: Episode V – The Empire Strikes Back → Star Wars

app/api/card/route.ts uses these shortened strings in its template search queries. Its scorer can rank only the supplied queries and has no minimum threshold before returning the top option. A model cannot recover the exact title if every relevant template omitted it. Preserve the full work title as the primary query; strip only known edition/series annotations. This is source-level retrieval specificity evidence, not a measured external-search relevance score.

## Ten new query outcomes

Seeded selection from ten fresh category-specific pools, not a representative accuracy benchmark. Real browser/provider responses.

| Query | Outcome | Cards | Loaded art |
|---|---|---:|---:|
| Adrianne Lenker | Pass | 5 | 3 |
| Stereolab | Pass | 5 | 5 |
| Greta Gerwig | Pass | 5 | 5 |
| Jorge Luis Borges | Pass | 5 | 1 |
| Converse | Pass | 4 | 0 |
| Amélie | Pass | 3 | 3 |
| The Fifth Season | Pass | 2 | 2 |
| Baldur’s Gate 3 | Pass | 4 | 3 |
| Succession | Pass | 3 | 3 |
| Copenhagen, Denmark intended | Failed identity assertion; unlabeled candidate also empty | 0 | — |

Nine completed intended flows, one failed intended journey. Across the nine primary completed maps:36 cards,36 visible connections,25 loaded images,11 absent images,zero failed/pending images in bounded snapshots. Do not include the New York control in these totals. Each completed flow covered details opening, save without graph expansion, saved count after reload and gallery access. This does not independently verify every credit, description or semantic fit.

## Prior defects freshly reproduced, not fixed

- Map heart: after hover, elementFromPoint at heart center returns card-hit. Overlay still blocks pointer saving. Details-panel save works.
- Removing disposable exploration: history entry gone, but IndexedDB retains session=true, two events, one edge. Local data retention, not remote exfiltration. Dialog's deletion promise remains too broad.
- Failed gallery/brief images: after bounded retries, image display:none and missing styling, but no icon/initial fallback; blank image areas remain.
- Provider factual prose issues and generic loose-match explanations documented in round21 remain open on unchanged code; their external facts were not independently rechecked in this round.

## Saving, exploration, RAG and UI regressions passed

- Lighthouse and Dark save/unlove/save, one saved item per map, persisted after reload; no expansion on saving.
- Resume Lighthouse: one saved signal, positive memory scoped to current map; agent three→eight cards, stream reports five additions.
- Rejected I'm Thinking of Ending Things remains absent after reload and agent expansion; in dislikes/exclusions, not positive memory. Three→two→seven cards.
- Gallery inspector hides Explore with Qloo.
- Home reachable/no horizontal overflow at320×568,390×844,768×1024,1440×900,844×390. Map no overflow at320/390/768/1440.
- Share focus/Tab containment, gallery focus restoration, mobile recents close44×44, three nested-confirm cycles pass.
- Exact-sharing fixture preserves descriptions. Long social links intentionally share seed-only, not the full map.
- Fixtures use explicitly authored maps in isolated browser storage, not fake recommendation success. No public shares posted.

## Security and server, freshly checked

- Public .env/.env.local/.git/config/server.js/package.json/app.env404; GET discover/agent405; null bodies400; foreign origin403; oversized body rejected400.
- Hostile shared-map HTML escaped; javascript links and HTTP metadata-service image dropped.
- Deployed public asset scan:39 files,zero skipped;two active runtime provider-key values checked,zero exact matches. No secret values printed. Not a scan of historic keys, logs, Git history or backups; key rotation not verified.
- Installed production inventory137 package names;zero npm advisories returned at check time. Not proof all packages are safe.
- App healthy on dedicated instance; deployed image9c18255; node non-root; read-only rootfs; app port8000 not host-published; secret file root-owned600; Caddy log rotation10MB×3.
- Disk75% used,2.0GiB free;401MiB available RAM;38MiB swap used. No cleanup/restart performed.
- Network firewall/IMDS were verified in round22 and not re-read in round23. Do not present them as new independent checks.
- No claim of zero vulnerabilities/leaks or prompt-injection immunity. Local retention above is a confirmed privacy defect despite no exposed runtime key found in the scoped scan.

## Validation and evidence

- Lint passes;49 individual unit tests pass.
- tests/live_queries_round23.py; /tmp/throughline-round23-results.json; /tmp/throughline-round23-run.log.
- tests/live_copenhagen_round23.py; tests/live_copenhagen_second_round23.py; corresponding /tmp/throughline-round23-copenhagen files.
- tests/live_card_cache_round23.py; /tmp/throughline-round23-card-cache.json.
- /tmp/throughline-round23-state.log; /tmp/throughline-round23-rejection.log; /tmp/throughline-round23-unit.log; /tmp/throughline-round23-lint.log.
- Fresh reused artifacts: /tmp/throughline-round22-deletion.json; /tmp/throughline-round20-art-failure.json; /tmp/throughline-security-round10.json; /tmp/throughline-round10-shared-safety.json; /tmp/throughline-round11-ui.json.

Priority: fix known map-heart and deletion defects, repair country-aware identity resolution, then make link-generation caches evidence-sensitive and keep exact titles. More random successes on unchanged code do not close these findings.
