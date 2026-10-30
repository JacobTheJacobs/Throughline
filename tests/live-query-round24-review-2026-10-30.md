# Round 24 — new deployment, ten live queries, UI/RAG/security review

Started October29, completed October30,2026 (Asia/Jerusalem). Production https://throughline.51-21-210-47.sslip.io. Local/deployed version c7179e3, including aca5fbf and f173131. Review only: no app fixes, deployments or infrastructure mutations. Read-only server checks used the AWS compute skill on the dedicated Throughline instance only.

## High — new Loved-animation race changes a different map

Confirmed twice in the actual production UI using two explicitly authored disposable maps in isolated browser storage. Both maps contain the same saved book, a legitimate cross-map condition.

1. Open map A → Gallery → Loved; unsave the book.
2. Before the 820ms dissolve completes, go home and resume map B.
3. Map B initially shows one saved item; after A's timer fires it shows zero, and the book is saved as liked:false.
4. IndexedDB records the unlove event under map B, even though the user acted on A.

Second run: switch completed in176ms; B saved count1→0; event `{kind:unlove, sessionId:race-b, entityId:race-shared-book}`. Source app/page.tsx gallery footer delays `likeNode(node)` without a root/epoch guard. `likeNode` reads current rootRef and mutates current nodes/taste. The reject timer already checks the originating root; the new Loved-unsave timer does not.

This is both visible saved-state corruption and wrong RAG feedback attribution, not a provider relevance issue. Capture the originating session, apply feedback immediately or guard/cancel delayed work when the root changes. Do not let decorative animation determine the eventual data mutation. Also cover quick home/resume and map switching with shared IDs in regression tests.

Evidence: tests/live_gallery_race_round24.py; /tmp/throughline-round24-gallery-race.json. No mocked provider recommendations, no real user profile changed.

## Previous fixes actually verified live

- Map hearts: normal pointer save and unsave both pass; overlay no longer intercepts them. Hit test can return SVG inside the button, not the old card-hit overlay.
- Remove exploration: deleted fixture's IndexedDB session absent, events0, edges0, recent entry gone. Previously session/events/edge remained. This checks the simple isolated session, not every shared-entity garbage-collection edge case.
- Gallery and brief failed artwork: retries end in hidden image plus meaningful initials tile. Both surfaces now show a fallback; old harness initially missed the brief's new art-initials class, which was corrected before judging it.
- New solid icon hearts present. Toast auto-dismiss is present in source; timing was not independently asserted this round.

## Ten fresh live queries

Seeded random choice within ten new category pools, not a representative accuracy benchmark. Real production provider responses.

| Query | Flow | Cards | Loaded art |
|---|---|---:|---:|
| Lorde | Pass | 5 | 4 |
| Gorillaz | Pass | 5 | 4 |
| Sofia Coppola | Pass | 5 | 5 |
| Terry Pratchett | Pass | 5 | 0 |
| Ben & Jerry’s | Pass | 4 | 0 |
| Her | Pass | 3 | 3 |
| A Wizard of Earthsea | Pass | 3 | 3 |
| Spiritfarer | Pass | 2 | 0 |
| What We Do in the Shadows | Pass | 3 | 3 |
| Vienna | Pass | 5 | 5 |

Ten primary flow passes, no fallback.40 cards,40 visible connections,27 loaded images,13 missing-artwork cards; zero failed/pending images in bounded snapshots. All ten completed opening details, saving without graph expansion, saved-count restoration after reload and gallery access. Those flows save through details and do not exercise the fast animated-unsave root switch; a 10/10 result does not invalidate the new race.

Flow pass is not a factual certificate for all descriptions, credits or recommendations. The 13 absent covers are provider/evidence coverage gaps, not failed URLs. Terry Pratchett, Ben & Jerry's and Spiritfarer maps remain visually sparse despite functional flows.

## Other remaining findings

- **Medium: link-generation cache still ignores richer identity evidence.** Fresh two-call live Dune/book control: first source=jev; second with creator/year/tags has identical cached options and omits source. app/api/card/route.ts cache key still id/name/type. Use sanitized evidence/version in cache keys and preserve provenance. Does not prove a specific external search result is wrong.
- **Medium: exact-title search specificity remains unresolved.** lib/card.ts shortName strips meaningful subtitles; source unchanged since round23's Spider-Man/Two Towers/Star Wars controls. No external search-engine retrieval benchmark conducted here.
- **Low/medium metadata granularity: a series is presented as one book.** Pratchett map includes Discworld type=book while its own description says fantasy book series. The author relationship is not shown to be false, but a series/subtype label would distinguish a catalogue from an individual read. Internal returned evidence is sufficient for this UI inconsistency; no separate bibliography fact-check performed.
- Copenhagen identity/coverage problem and source-prose factual issues from previous rounds were not retested here. No discovery/identity code changed in these three commits; do not mark them fixed solely because unrelated queries passed.
- **Medium operations warning: root disk now81% used,1.6GiB free**, versus75%/2.0GiB previously. The app is healthy; no cleanup or image deletion done. Inspect retention before further builds.

## Saving, RAG and UI controls

- Lighthouse/Dark ordinary save→unlove→save, independent counts, reload persistence pass; no expansion from saving.
- Resume Lighthouse: one saved signal, current-map memory isolation; agent three→eight cards, reports exactly five additions.
- Reject I'm Thinking of Ending Things: survives reload, sent in negative/exclusion lists, absent from positive memory and subsequent additions. Three→two→seven cards.
- Ordinary map isolation passes; the rapid animated-unsave switch is a distinct failing path.
- Gallery details hide Explore with Qloo.
- Home reachable/no overflow at320×568,390×844,768×1024,1440×900,844×390. Map no overflow at320/390/768/1440.
- Share focus/Tab containment, gallery focus restoration, mobile recents close44×44 and three wait-aware nested-confirm cycles pass. Fast fixture once sampled before scheduled focus; not counted as a confirmed focus escape.
- Exact shared-map fixture preserves descriptions. Long social sharing intentionally seed-only, not full map.

## Security and dedicated server, freshly checked

- Public .env/.env.local/.git/config/server.js/package.json/app.env404; wrong API methods405; null bodies400; foreign origin403; oversized discover body rejected400.
- Shared hostile HTML escaped; javascript links and HTTP metadata-service image dropped.
- Deployed public assets:39 files scanned,zero skipped;two current provider-key values checked,zero exact matches. No secrets printed. Historic keys/Git/logs/backups and rotation not audited.
- Installed production dependency inventory137 package names;zero advisories returned by npm registry at check time. Not a guarantee of vulnerability absence.
- App healthy, deployed c7179e3; non-root node, read-only rootfs, port8000 not host-published. Secret file root-owned600. Caddy log rotation10MB×3.
- Available RAM468MiB,swap40MiB used; disk81%/1.6GiB free.
- Firewall/IMDS/encrypted-volume checks from earlier rounds not independently repeated; no configuration writes made.
- No blanket “nothing leaks” or prompt-injection immunity claim. Bounded security checks passed, while the saved-state/RAG race above is a real correctness defect.

## Validation and artifacts

Lint passes;49 individual unit tests pass.

- tests/live_queries_round24.py; /tmp/throughline-round24-results.json; /tmp/throughline-round24-run.log.
- tests/live_gallery_race_round24.py; /tmp/throughline-round24-gallery-race.json.
- Updated harnesses: tests/live_delete_memory_round22.py now performs real pointer save/un-save; tests/live_art_failure_round20.py recognizes both old/new brief fallback classes.
- Fresh reused outputs: /tmp/throughline-round22-deletion.json; /tmp/throughline-round20-art-failure.json; /tmp/throughline-round23-card-cache.json; /tmp/throughline-security-round10.json; /tmp/throughline-round11-ui.json.
- /tmp/throughline-round24-state.log; /tmp/throughline-round24-rejection.log; /tmp/throughline-round24-unit.log; /tmp/throughline-round24-lint.log.

Priority: guard the delayed Loved-unsave mutation against root changes; then address identity/cache correctness and disk retention. The prior heart/deletion/artwork fixes should stay closed within their tested scope, rather than being carried forward as stale findings.
