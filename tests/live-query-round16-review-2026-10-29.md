# Throughline live review — round 16, 29 October 2026

## Summary

Ten fresh seeded live queries: **nine completed browser flows, one intended-brand resolution failure**. Successful maps contained **37 cards, 37 visible connections, 33 loaded covers**, four absent-image fallbacks, zero failed/pending image elements at the final sample. No provider responses mocked.

The previously failing Scotland depth1/depth2 control now passes live. A remaining geographic-region counterexample is confirmed locally in the actual exported helper. No newly demonstrated public credential exposure or runtime advisory in this bounded review. No application edits/deployment made; only review files added.

## Findings

### Medium — explicit category intent is not respected in clarification recovery

The random **Freitag** brand case did not surface the intended brand. It offered a FREITAG flagship store and mostly Friday the 13th movies. The harness correctly reports FAIL rather than choosing a different entity and calling it success.

Two additional real API controls:

- `Freitag brand` still offered mostly Friday the 13th movies and the store, with no Freitag brand.
- `FREITAG bags` offered Freaky Friday, the flagship store, an unrelated bag brand, an album and other places.

This does not establish that a suitable Freitag brand exists in Qloo; provider coverage remains unverified. The application issue is recovery: explicit `brand` intent should not turn into a mostly-movie meaning chooser. `app/api/discover/route.ts:291–298` only uses the preferred type when an exact match exists; otherwise the fallback pool contains all types. Preserve the requested type and explain missing coverage, or distinctly label broader alternatives. Do not fabricate a brand to fill the gap.

### Medium — region enforcement disappears when every returned place has the wrong region

The new helper at `lib/geography.ts:10–18` rejects a conflicting region only when the selected region occurs somewhere in the returned batch. `tests/geography_scope_round16.mjs` exercises the actual production helper with explicit synthetic evidence:

```
selected: Ontario, Canada
returned: [Vancouver, British Columbia, Canada]
regionAppears: false
accepted: true
expected: false
```

This is a local counterexample, not a newly observed wrong-country live result. The current unit fixture includes a Toronto result in the same batch, which sets regionAppears=true and misses this all-wrong-batch case. A selected region should not lose its constraint because retrieval failed to return evidence for it. If administrative names cannot be verified, return uncertain/unsupported coverage rather than treating shared country as regional confirmation.

### Lower-priority output/UI quality

- Four absent-cover fallbacks: one Elena Ferrante reference, one House of Leaves reference, two Inscryption references. No broken/pending images at the 15-second settle sample.
- House of Leaves returned only two explicitly looser matches. Their explanation says “a looser match than the verified ones,” although this batch has no strict matches. Prefer an unconditional “Looser match” label without implying other results exist.
- Candidate profile/tag text does not always explain the specific shared subject JEV accepted; do not present candidate mood as independently proven causal relevance.
- Long social links remain explicitly starting-point-only. Copy exact link preserves descriptions and the map. This is a disclosed product limitation.
- No new reproducible modal keyboard failure: the old fast fixture intermittently measured confirmation focus outside before its animation-frame focus completed. A wait-aware follow-up repeated three open/8-Tab/Escape cycles; all tabs stayed inside and opener focus restored. Report timing sensitivity in the old harness, not a confirmed persistent focus escape.

## Ten random live cases

Stratified random seed `2026102916`; concurrency two, isolated contexts, form submission. The destination requires a New Zealand description, preventing a namesake from being counted as the desired place. Flow checks cover identity choice, duplicate/source exclusions, explanation presence, visible edges, opening cards, no graph growth on Save, reload persistence and Gallery.

| Query | Flow | Cards | Loaded art | Edges |
| --- | --- | ---: | ---: | ---: |
| Angel Olsen | Pass | 5 | 5 | 5 |
| The War on Drugs | Pass | 5 | 5 | 5 |
| Jim Jarmusch | Pass | 5 | 5 | 5 |
| Elena Ferrante | Pass | 5 | 4 | 5 |
| Freitag | Intended brand not surfaced | 0 | 0 | 0 |
| Sound of Metal | Pass | 2 | 2 | 2 |
| House of Leaves | Pass; two labeled looser matches | 2 | 1 | 2 |
| Inscryption | Pass | 3 | 1 | 3 |
| Andor | Pass | 5 | 5 | 5 |
| Wellington, New Zealand | Pass | 5 | 5 | 5 |
| **Total** | **9 completed, 1 failure** | **37** | **33** | **37** |

These are not statistical recommendation-accuracy scores. All factual credits were not independently audited. Fewer than five results is not by itself a defect; distinct adaptations/albums sharing titles are not automatically duplicates.

## Previously failing geographic control

`tests/live_geography_round15.py` now passes on production for Scotland ID `A75E2277-6EDF-4E18-831C-096E806E51AE` at both depth1 and depth2. Both return Royal Botanic Garden Edinburgh, Edinburgh Castle, Camera Obscura & World of Illusions, Edinburgh Festival Fringe Society and The Dome. No Indiana links appear. This closes the recorded nested Scotland regression, not every geographic alias/administrative hierarchy case.

## Saving, exploring and browser-local retrieval

- The Lighthouse/Dark: save→unsave→save, reload, no Save-driven expansion and Gallery hiding Qloo exploration passed.
- Resuming The Lighthouse sent one map-local saved signal and no positive anchor from the other map.
- Agent run: **3→8 cards**, streamed and reported five additions.
- Rejected I'm Thinking of Ending Things remained absent after reload, was sent in dislikes/excludeIds, was not positive memory and was not reintroduced. After removal,2→7 cards following exploration.
- These checks do not establish all simultaneous-tab ordering, alias or edition cases. No new population JEV benchmark was run.

## Security/server/verification

- Fourteen bounded exposure/input probes passed: sensitive paths404, unsupported GET405, null bodies400, foreign Origin403, oversized JSON400.
- Authored shared-map HTML/event handlers did not execute; javascript links and HTTP metadata-address images were removed. Not a comprehensive injection/SSRF audit.
- Exact current runtime-key scan: **two values**, **39 deployed public files**, zero skipped, **zero matches**. No values printed. Rotation and private logs/history are not verified by this scan.
- Installed runtime inventory: **137 package names**, zero advisories from npm registry bulk endpoint. Known-advisory coverage, not absence-of-vulnerabilities proof.
- Production image `2026-10-29-7ac0b8d`, health healthy, user=node, read-only rootfs, app port unpublished. Secretfile600/root. Caddy rotation10MB×3. Disk70% used,2.4GiB free. Other EC2s untouched.
- Filesystem budget contention:400 admitted,200 capped,zero busy,final ledger400. No provider calls. Does not exhaust stale-lock/crash conditions.
- Lint and **47 individual unit tests** passed. Synthetic geography scope counterexample remains outside those assertions.
- Share initial focus/Tab containment, description preservation, Wikidata badge, gallery focus restoration and44×44px Recents close passed. Wait-aware nested modal3×8Tabs passed.
- Home reachability/no-overflow at320×568,390×844,768×1024,1440×900,844×390 and map overflow320/390/768/1440 passed. This is not full accessibility conformance.

## Reproduction/evidence

- `tests/live_queries_round16.py`; `/tmp/throughline-round16-results.json`.
- `tests/geography_scope_round16.mjs` (synthetic helper counterexample).
- `tests/live_confirm_round16.py` (wait-aware production keyboard check).
- `/tmp/throughline-round16-freitag-controls.json` (real API identity controls).
- Existing geographic/state/rejection/security/sanitization runners rerun; corresponding `/tmp` outputs refreshed.
- Sanitized server inspection/scan command `d0ef4309-9dfc-4043-b638-8489f89b13de`.

No claim that “nothing leaks,” “all queries work,” or “all recommendations are accurate.” No production changes in this review.
