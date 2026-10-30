# Music discovery recovery — implementation and live verification

Date: 2026-10-28. Changes build on `f3bf0ff`; no commit was created.

## Implemented

- Music-title searches that otherwise expose only album releases also offer exact, source-linked musical works. Explicit `song` searches offer songs only and never send Qloo's unsupported `urn:entity:song` search filter.
- The chooser distinguishes Dragostea din tei's O-Zone and Haiducii versions using their separate Wikidata identities, descriptions, performers and dates. No artist/song names are hard-coded in application logic.
- Unresolved musical works can offer **Find matches from [artist]** only after a real P175 performer edge and a matching artist identity/name are established. This is a user-selected change of recommendation anchor, not a silent song-to-artist substitution.
- Title-only music crosswalks are prohibited. A namesake album, remix, or similarly named artist cannot inherit another work's identity just because its title is unique in a small search result.
- Invalid Qloo interest anchors are distinguished from empty categories and unrelated provider errors. Once a work cannot anchor discovery, all category states are blocked; subset responses no longer bring dead buttons back.
- The unresolved-work inspector replaces category buttons with an explicit action from the map's named starting reference. Hot n Cold can continue through Katy Perry without discarding the existing map.
- Unlinked musical works skip speculative category ranking; a single anchor check establishes whether category exploration is possible. Known blocked records do not repeat category probes on subsequent clicks.
- Home/resume transitions invalidate stale requests, clear old recovery/chooser states, and discard stale previous-map restoration state. Opening a card also dismisses unrelated recovery overlays.

## Real live results

`PYTHONDONTWRITEBYTECODE=1 python3 tests/live_music_recovery.py` passed on the final tested implementation:

1. Dragostea query offers both source-identified versions. Choosing the O-Zone song does not silently create a different map; explicitly choosing its artist recovery produces **five recommendations**, with **O-Zone** named as the starting reference.
2. Choosing the exact older Qloo album entry still reports its genuine unsupported-anchor limitation and offers another meaning. Resuming the O-Zone map clears the unrelated failed-search overlay.
3. Katy Perry opens with five works. Hot n Cold triggers **one** anchor probe and shows **zero category buttons** after that check. Explicitly finding matches from Katy Perry grows the existing map **5 → 10**, without the Dragostea overlay or browser errors.
4. The resulting map has no horizontal overflow after changing the viewport to **390 × 844**. This is a narrow-screen smoke check, not a full responsive certification.

Additional real API checks:

- `Dragostea Din Tei song`: two distinct song choices, both with performer descriptions.
- O-Zone's song identity: HTTP 422 `no_qloo_identity`, now accompanied by a verified O-Zone recovery anchor rather than a dead end.
- The original album entry's artist probe: HTTP 200 with `unsupported_anchor` and artist availability `unsupported`, rather than a misleading empty-results or provider-outage classification.
- Blue Monday: verified song choice and a source-linked **New Order** recovery anchor, demonstrating that the code is not specific to the reported title.

An intermediate stricter crosswalk rejected O-Zone because Qloo's secondary MusicBrainz ID differed from Wikidata's, despite its exact linked Wikidata item and matching artist name. The final rule requires matching primary Wikidata identity plus name; a conflicting primary item cannot be rescued by a secondary ID. MusicBrainz is an alternative only when the provider has no primary Wikidata item. Regression tests cover those distinctions.

## Validation and limits

- Lint, unit tests, TypeScript checking, production build and `git diff --check`: passed.
- Added pure tests for exact work matching, remix separation, missing/deprecated performer links, artist identity conflicts, invalid IDs, and invalid-anchor error classification.
- No relevance thresholds, quota limits, credentials or provider results were relaxed or fabricated.
- Qloo still does not support the reported song/release as an audience anchor. The implementation supplies an honest, actionable recovery; it does not claim to add provider coverage.
- Artwork delivery/CSP and the other independently reported Round 9 findings are outside this change and are not claimed fixed.

Raw evidence, including the intermediate failure and final passing rerun: `/tmp/sideways-music-recovery-fix-evidence.json`. Browser regression: `tests/live_music_recovery.py`. Narrow-view screenshot: `/tmp/sideways-music-recovery-fixed.png`.
