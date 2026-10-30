# Throughline follow-up review — 2026-10-29

Scope: current local source, production-browser synthetic shared-map fixture, read-only SSM server inspection, lint and unit tests. No deployment, application edits, paid-provider accuracy tests or credential rotation in this pass.

## Priority findings

### High: the new durable budget fails open

`lib/guard.ts:20–26` silently ignores unreadable/malformed state and write errors. A fresh module/process starts another allowance when the configured state path cannot be written. Offline guard-only reproduction used a nonexistent parent directory under `/tmp`, 401 requests with distinct synthetic IPs, then a fresh module instance. Each instance allowed 400 agent requests and rejected request 401: 800 allowed in total despite the purported persistent 400-request ceiling. No provider calls were made.

Persistence also writes JSON directly rather than atomically, saves at most once per five seconds without a final flush, and loads only once per process. Crashes can lose recent counts; concurrent old/candidate processes can hold independent stale counters. Request counts are not a measured dollar/token budget. Treat storage failure explicitly and use transactional reservations if a hard aggregate ceiling is required.

### Medium: local fixes are not verified as deployed

The live browser still reports shareInitialFocusInside=false, shareTabWrapInside=false, descriptionSurvivesSharing=false, factualBadge=Qloo and galleryFocusRestored=false. Several corresponding changes exist locally: share ref/Tab handling, description inclusion, factual Wikidata badges. Do not call these fixed in production until the deployed version passes the browser checks.

Read-only SSM command `42ca1d10-2183-4c2a-bde0-65ca1b63e7c4` also found no `.State.Health` entry for the live app (the health-state template returned a missing-key error), while the local deployment script now specifies a healthcheck. Caddy still reports json-file logging with empty options. Disk is 62% used, 3.1 GiB free; three stopped rollback containers remain. No claim is made about current AWS alarms or OS patch status because they were not rechecked.

### Medium: social sharing still reduces the map

`app/page.tsx:359` retains the 1,800-character threshold and seed-only fallback. Local code now warns after opening the social window, which is an improvement, but the pre-action dialog still promises the exact graph. The live 12-reference authored fixture produced a 4,477-character exact link; social sharing used the starting point only. Make the reduced action explicit before opening it or preserve the snapshot.

### Medium: gallery focus fallback can still select a hidden map control

`app/page.tsx:224` selects the map card first and uses the gallery opener only when the map element is absent, not when it is hidden. If both DOM representations exist in gallery mode, the hidden map control wins and focus fails. Live test confirms focus is not restored; local source still uses this null-only fallback. Select the opener by active view or retain the actual triggering element.

### Low: brand icons and mobile hit area remain inconsistent

The local share markup still uses text glyphs `𝕏`, `r/`, and `◉` instead of the requested brand icons. The live recent-history close control measures 30×30 px. This is a usability finding, not by itself a WCAG violation claim.

## Verification and qualifications

- Lint completed without reported errors.
- All 43 individual unit tests passed outside the restricted sandbox; direct execution also reports 43 passes. The sandboxed child-process runner misleadingly displayed a single file-level pass, so that output was not used as proof of 43 tests.
- Production browser tests used the existing explicitly authored fixture, not real recommendation outcomes; clipboard/social opening was intercepted.
- Nested confirmation focus failed on this run, unlike the previous run. Treat as unstable evidence requiring a wait-aware targeted test before declaring a regression.
- Local deployment now arms an EXIT rollback handler before cutover and bounds archived containers. The old offline harness reaches its injected rename failure and logs a restart, but also attempts an unstubbed `/opt/sideways` mkdir; it is no longer fully hermetic and must be updated before treating it as a comprehensive deployment regression test. The attempted mkdir failed read-only; production was not touched by the harness.
- A Docker healthcheck is detection, not automatic restart of an unhealthy running container. No recovery controller was identified in this local update script.
- Existing key-rotation verification remains open. This pass establishes no new public secret leak and does not establish that no leak exists.

No production or application changes made during this review.
