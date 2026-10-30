# Round 22 — live discovery, UI, local data retention and security review

Date: 2026-10-29. Target: https://throughline.51-21-210-47.sslip.io

Local and deployed image still 9c18255. No application or server changes made; review scripts/report only. Other EC2 instances not operated on.

## New confirmed findings

### High UX impact — map heart cannot receive pointer clicks

On the production UI, a normal click on the authored fixture's map heart repeatedly failed because `.card-hit` intercepted the pointer. After hovering the card, elementFromPoint at the heart's center still returned `card-hit`. Source corroborates the stacking: `.card-hit` z-index6 at app/globals.css:137; `.card-taste` z-index4 at app/globals.css:297. This is not a provider/algorithm failure. The details-panel save button works, as does gallery saving, so prior tests that saved only through details missed it. Put map actions above the full-card hit target and test real pointer clicks, not forced clicks or DOM dispatch.

Evidence: tests/live_delete_memory_round22.py, first run's Playwright interception trace and second run's HEART_HIT_TEST output. Authored disposable map in a fresh browser context; actual production UI, no provider response mocked. Not independently repeated on touch hardware.

### Medium privacy/data lifecycle — removing an exploration leaves its taste memory

The live isolated deletion test created and saved a disposable reference, returned home, opened the exploration menu, and confirmed Remove exploration. The recent entry disappeared, but IndexedDB still contained the same session, two events and one edge. The dialog says the saved map and references on this device will be deleted. `removeSession` at app/page.tsx:261 removes history and two localStorage keys, not IndexedDB entities/edges/events/sessions.

This is local retention, not evidence of exfiltration. Because taste-memory retrieval is keyed by the root ID, retaining this history also creates a stale-preference risk when that root is explored again; reuse of the old signal was not separately demonstrated in a new provider request. Implement session-aware deletion, preserving entities shared by other maps, or explicitly label the action as history-only and offer a real delete-data control.

Evidence: /tmp/throughline-round22-deletion.json: before {session:true, events:2, edges:1}; after removal identical, historyEntryGone:true. No real user browser profile or server records deleted.

### Medium visual quality — failed artwork still becomes blank space

Fresh controlled browser failure test confirms gallery and brief images retry then display:none, with art-missing styling, but no initial/icon fallback is rendered. Broken-image symbols are resolved; meaningful placeholders are not. Missing cover URLs are a separate coverage issue: nine of this sample's cards had no loaded art, including all five Susanna Clarke works. Do not insert unrelated artwork to conceal this.

### Coverage friction — IKEA's factual starting path requires recovery

IKEA returned a no-linked-identity message instead of direct works/products; Try audience matches then produced five results. Those include George Michael and Bryan Adams, explicitly labelled audience overlap, not a subject match. Do not call them factual IKEA connections. This is an identity/coverage gap with an honest recovery, not an observed crash or proof those audience affinities are false.

### Existing accuracy findings are not resolved by this review

The code remains unchanged since round21. That round's confirmed provider-prose errors and generic looser-match explanations remain open. The new ten-query flow pass is not an independent fact-check of every returned description or credit. No new authoritative external fact-check was conducted in round22; see round21 for primary-source evidence. JEV uses supplied descriptions as evidence and is not a source-of-truth verifier.

## Ten fresh live queries

Seeded selection from ten category-specific pools. Not a representative accuracy sample. No mocked recommendations.

| Query | Outcome | Cards | Loaded artwork |
|---|---|---:|---:|
| St. Vincent | Direct flow pass | 5 | 4 |
| Sigur Rós | Direct flow pass | 5 | 4 |
| Wong Kar-wai | Direct flow pass | 5 | 5 |
| Susanna Clarke | Direct flow pass | 5 | 0 |
| IKEA | Explicit audience recovery, then pass | 5 | 5 |
| The Grand Budapest Hotel | Direct flow pass | 2 | 2 |
| Beloved | Direct flow pass | 3 | 3 |
| Hades | Direct flow pass | 3 | 1 |
| Atlanta | Direct flow pass | 3 | 3 |
| Kyoto | Direct flow pass | 5 | 5 |

Nine primary passes, one fallback, zero unsuccessful searches. Total 41 cards, 41 visible edges, 32 loaded images, nine absent images, zero failed/pending images in bounded visual snapshots. All completed opening details, saving without graph growth, saved-count restoration and gallery access. These use details-panel saving, which is why the separate pointer test matters.

## Saving, agent and RAG memory regressions

- Live Lighthouse and Dark: save → unlove → save; each shows one saved reference independently, survives reload, no graph expansion on save.
- Gallery Explore with Qloo hidden; saved gallery filters/newest order pass on authored fixture.
- Resume Lighthouse: one saved signal; positive memory scoped to the map. Agent changes three cards to eight and reports exactly five additions.
- Reject I'm Thinking of Ending Things: absent after reload; sent in dislikes/excludeIds, absent from positive memory; not reintroduced by agent. Three → two → seven cards.
- These successes coexist with retained memory after deleting an entire exploration. Do not confuse per-reference rejection with session deletion.

## UI and accessibility checks

- Responsive home: no horizontal overflow, search reachable at 320×568, 390×844, 768×1024, 1440×900 and 844×390.
- Map no horizontal overflow at 320/390/768/1440. Gallery at same widths passes.
- Two-line gallery titles, 44px hearts and filter targets, populated filters and aria-pressed remain present. Inspected fresh 390px gallery screenshot.
- Share initial focus and Tab containment, gallery focus restoration, mobile recents close44×44, and three nested-confirm keyboard cycles pass.
- Remaining small header targets documented in round21; no app changes since then.
- Real map-heart pointer interaction fails despite keyboard/dialog checks passing. Broad “accessibility passed” claims would therefore be misleading.

## Security and dedicated server — freshly checked

- Public .env/.env.local/.git/config/server.js/package.json/app.env return404. Wrong methods405; null API bodies400; foreign origin403; oversized discover body rejected400.
- Authored hostile shared map: HTML escaped; javascript links and HTTP metadata-service image dropped.
- Counts-only deployed scan: 39 public files, zero skipped, two active runtime provider-key values checked, zero exact matches. Does not cover all historic keys, logs, Git history or backups. Rotation not verified.
- Actual installed production dependency inventory:137 package names, zero advisories returned by npm registry at check time. Not proof of zero vulnerabilities.
- Live security headers present: CSP, HSTS, nosniff, frame denial, restrictive permissions/referrer. CSP retains unsafe-inline scripts; no nonce migration done.
- Dedicated instance running, IMDSv2 required; firewall only80/443 IPv4/IPv6.
- App healthy; non-root node; read-only rootfs; port8000 not host-published. Secret file root-owned600. Caddy log rotation10MB×3.
- Disk75% used, 2.0GiB free; available RAM447MiB, swap38MiB used. No cleanup/restarts performed.
- Local budget contention test:600 reservations,400 allowed,200 capped, ledger400, no busy failures. Uses temporary local file; does not spend production allowances.
- This is bounded hardening/leak review, not a complete penetration test, prompt-injection proof, or guarantee that nothing leaks. The local-retention defect above is a real privacy issue even though no remote secret exposure was found.

## Validation and artifacts

- Lint passes;49 individual unit tests pass.
- tests/live_queries_round22.py; /tmp/throughline-round22-results.json; /tmp/throughline-round22-run.log.
- tests/live_delete_memory_round22.py; /tmp/throughline-round22-deletion.json.
- /tmp/throughline-round22-state.log; /tmp/throughline-round22-rejection.log.
- /tmp/throughline-round22-unit.log; /tmp/throughline-round22-lint.log; /tmp/throughline-round22-gallery.log.
- Fresh reused runner outputs: /tmp/throughline-security-round10.json; /tmp/throughline-round10-shared-safety.json; /tmp/throughline-round11-ui.json; /tmp/throughline-round20-art-failure.json and screenshot; /tmp/throughline-round19-gallery-390.png.

Priority: fix pointer stacking and make exploration deletion match its promise; then complete artwork fallbacks and address independent verification of provider prose. No fixes implemented in this review-only turn.
