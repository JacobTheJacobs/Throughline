# Round 21 — live discovery, UI, security and dedicated-server review

Date: 2026-10-29. Production image: `2026-10-29-9c18255`, matching the reviewed local commit. No application fixes, deployment, credential rotation or infrastructure changes performed. Only review scripts/reports changed. Other EC2 instances were not operated on.

## Ten new queries

Seeded selection from ten fresh category pools, not a representative random accuracy benchmark. Real production providers and browser flows, no mocked recommendations.

| Query | Outcome | Cards | Loaded artwork |
|---|---|---:|---:|
| Sufjan Stevens | Pass | 5 | 4 |
| Big Thief | Pass | 5 | 5 |
| Céline Song | Pass | 2 | 2 |
| Octavia Butler | Pass after explicit harness alias control | 5 | 0 |
| Uniqlo | Pass | 1 | 0 |
| Moonlight | Pass | 3 | 3 |
| The Dispossessed | Pass; includes labelled looser matches | 4 | 4 |
| Tunic | Pass; includes labelled looser matches | 3 | 1 |
| Reservation Dogs | Pass | 3 | 3 |
| Reykjavík | Pass | 5 | 5 |

Original automated run: nine passes and one harness failure. The chooser correctly offered Octavia E. Butler, but the test did not recognize the inserted middle initial. An explicit person/alias control selected the offered American science-fiction writer and passed. This is not an app search failure; both the original run and control are retained. The chooser also offered same-name person/author entries, which can still make selection unnecessarily confusing.

Final combined sample: 36 cards, 36 visible edges, 27 loaded images, nine absent-image tiles, zero failed/pending images in bounded snapshots. Opening details, saving without graph growth, saved count after reload and gallery access passed for all ten completed flows. Flow success does not certify every fact or semantic recommendation.

## Remaining findings

### High — returned descriptions still contain factual errors

Reservation Dogs returned Somebody Somewhere with a description saying Hannah Bos and Paul Thureen directed the series. HBO identifies them as creators; its release credits Jay Duplass and Robert Cohen as directors. This is a confirmed content defect, not proof the recommendation itself is inappropriate. See [HBO's official series release](https://press.wbd.com/us/media-release/hbo-0/hbo-original-comedy-series-somebody-somewhere-starring-and-executive-produced-bridget).

The same search returned I'm a Virgo with a Los Angeles setting. The [Louisiana film-production authority's project page](https://www.louisianaentertainment.gov/project/im-a-virgo) identifies Oakland, consistent with the [City of Oakland's production report](https://www.oaklandca.gov/files/assets/city/v/1/public-meetings/oakland-workforce-development-board/2024/oakland-workforce-development-board-agenda-packet-5-2-24.pdf).

The present JEV gate compares supplied evidence for relevance; it is not independent verification of that evidence. The provider descriptions can therefore feed false details into later relevance decisions. A generic fit score or “verified connection” must not imply all prose is verified. Prefer sourced structured credits and narrowly scoped summaries; do not patch two descriptions and assume the systemic issue is solved.

### Medium — artwork failure handling is only partly resolved

Controlled browser-only aborted image requests now retry and finally hide the image. The broken-image symbol is gone. However, gallery and brief retain the hidden failed image without rendering their intended icon/initial fallback. Both have display:none and an art-missing class; screenshot shows a blank beige image area. The first fast snapshot was too early, before backoff; final post-retry evidence supersedes it.

This is separate from missing art: Octavia's five books, Uniqlo's sole person card and two Tunic matches lacked images. Those are coverage gaps, not broken URLs. Intentional placeholders should still identify category and title.

### Medium — looser recommendations need concrete, inspectable explanations

The Dispossessed returned Trapped as a looser match, justified only by “shares some of its subject or themes.” That does not tell a user which distinctive connection was supported. Source review confirms a separate lower gate (`subject >= .45`, margin >= .05) can admit labelled related cards after strict results are sparse. The label is honest, but it does not establish accuracy or explain the actual bridge. Treat Trapped as a manual semantic-review candidate, not a proven false match or a confirmed good one. Explanations should name the supported common idea; otherwise offer the result explicitly as audience-only or omit it according to the requested mode.

### Low — remaining small header targets

Gallery hearts and filters are now at least 44px, and titles allow two lines. Header home remains 36–38px high; mobile Share is 40px wide and tablet Share 40×40. These remain below a comfortable 44px touch target, not an asserted WCAG AA violation. Gallery title buttons can be ~33px high, but the larger image is an alternative opener.

### Low — disk headroom

Dedicated server root disk is 75% used with 2.0GiB free. It is healthy, not full. Keep future image/build retention bounded; no cleanup was performed during this review.

## Fixes verified and behaviour tests

- Deployed commit matches local 9c18255.
- Gallery hearts and category filters enlarged; two-line titles; zero-result categories hidden; selected filters now have aria-pressed (source inspection).
- Black Dog remains song before and after live reload.
- Save → unlove → save gives one saved reference; does not add cards.
- Lighthouse and Dark save counts stay separate, persist after reload, and gallery details hide Explore with Qloo.
- Resume Lighthouse: one saved signal; retrieved positive memory scoped to that map. Agent changes three cards to eight; stream reports exactly five additions.
- Rejected I'm Thinking of Ending Things remains absent after reload and subsequent exploration; sent in dislikes and excludeIds, not positive memory. Map changes three → two → seven without reintroducing it.
- No horizontal overflow in home checks at 320×568, 390×844, 768×1024, 1440×900 and 844×390; map at 320/390/768/1440. Gallery checks at 320/390/768/1440 passed.
- Share focus containment and gallery focus restoration pass. Fast nested-confirm fixture intermittently samples before scheduled focus; wait-aware three-cycle check passes. Do not report this timing artifact as a reproduced focus escape.
- One state test and one music test initially timed out waiting for cards. Independent URL control and retries passed. The original timeouts remain unresolved reliability observations; no evidence here establishes quota exhaustion or a deterministic code defect.

## Security and server checks

Read-only, bounded inspection of dedicated `i-0548ced6e50a6ecbc` only:

- EC2 system/instance checks OK; app healthy, non-root node user, read-only root filesystem; app port 8000 not host-published.
- Firewall ingress only 80/443 for IPv4/IPv6. Host sshd listens, but no port-22 ingress rule in this security group.
- IMDSv2 required; attached 8GiB gp3 disk encrypted.
- Caddy logs rotate 10MB × three files. Secret file /opt/sideways/app.env is root-owned mode600.
- ~450MiB available RAM; 38MiB swap used; root disk 2.0GiB free.
- 39 deployed public files scanned, zero skipped, zero exact matches for two active runtime provider-key values. No key values printed. This is not a scan of every possible secret, historic Git objects, logs or backups; rotation was not verified.
- Actual installed production inventory: 137 package names, zero advisories returned by npm's bulk registry endpoint at check time. Not a guarantee of vulnerability absence.
- .env/.env.local/.git/config/server.js/package.json/app.env all404; wrong API methods405; null JSON bodies400; foreign origin403; oversized discover body rejected400.
- Shared-map HTML rendered as text; unsafe javascript links and HTTP metadata-service image removed in browser fixture.
- Live HTTPS response has CSP, HSTS, nosniff, frame denial, restrictive permissions and referrer policy. CSP still allows unsafe-inline scripts, so it is defense-in-depth rather than nonce-based XSS isolation.
- Source review: bounded JSON reader, same-origin validation, per-IP and persisted service budgets; artwork redirects allowlisted; JEV fixed endpoint, finite bounded scores and untrusted-data instructions. These do not constitute a full penetration test or robust proof against prompt injection.

## Local validation and evidence

- npm run lint passes.
- npm run test:unit passes; direct invocation confirms 49 individual tests pass (the test runner wrapper reports one file-level test).
- Ten-query runner/results: tests/live_queries_round21.py; /tmp/throughline-round21-results.json; /tmp/throughline-round21-run.log.
- Explicit alias and URL controls: tests/live_controls_round21.py; /tmp/throughline-round21-alias.json; /tmp/throughline-round21-controls.log.
- State retry: /tmp/throughline-round21-state-retry.log. Rejection: /tmp/throughline-round21-rejection.log.
- Updated image harness: tests/live_art_failure_round20.py; /tmp/throughline-round20-art-failure.json and screenshot. It now waits for post-backoff state using CSP-compatible protocol polling.
- Fresh gallery fixture: /tmp/throughline-round19-gallery.json and screenshots (reused runner filenames).
- Public security probes: /tmp/throughline-security-round10.json. Responsive/keyboard fixtures use prior filenames, freshly executed.

Bottom line: tested flows and deployed hardening are substantially sound within this scope, but “all accurate” and “nothing leaks” are not supported absolute claims. Provider factual prose and concrete explanations remain the most important quality gaps.
