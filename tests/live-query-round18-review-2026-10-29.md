# Throughline live review — round 18, 29 October 2026

## Verdict

The previously recorded Québec City, nested Scotland, Ontario and Île-de-France regressions pass their controls. Ten fresh intended entities were explored; the original runner completed nine and rejected a correct brand alias, then an explicitly alias-aware control completed the tenth.

Two accuracy issues remain: a live music card changes category after reload, and a returned provider description contains independently checked factual errors. These are not proof of an exploit or that every recommendation is irrelevant. No implementation or production changes made in this pass; only review files added.

## Confirmed findings

### Medium — music classification changes after reload

The real Arlo Parks search returns Black Dog (`wikidata:Q96072224`) as `album` even though its own description is `song by Arlo Parks`. A targeted browser control then observed:

```
initialType: album
restoredType: song
stable: false
```

The same node ID changes category without a new user choice. `wikidataWorkType` can prioritize an album instance ID during server retrieval, whereas `repairDirectConnection` reclassifies restored musical items from description alone. Normalize the work-versus-release distinction consistently across initial rendering, restoration, category filtering and exploration. Do not hardcode this title. A streaming API may model a single as an album-shaped release container; that does not justify changing the UI identity after refresh.

Reproducer: `tests/live_music_type_round18.py`. Public artist/label music listing confirms a single release: [Black Dog on Spotify](https://open.spotify.com/album/7g57U9ugd9ObC65ecCeEHy), [Apple Music listing](https://music.apple.com/us/album/black-dog-single/1502254966).

### Medium — provider descriptions are not fact-checked by the relevance gate

The live Leftovers result for Station Eleven describes a six-part series and names Patrick Somerville as director. HBO's official press release describes ten episodes and identifies Somerville as creator/showrunner, with Hiro Murai directing. The metadata therefore contains factual errors even though the recommendation may be a useful thematic connection.

JEV evaluates thematic fit using the supplied evidence; it does not independently validate that evidence's credits or episode counts. Keep verified identity/affinity, imported descriptive prose and independently corroborated facts separate in claims and UI. Prefer authoritative structured metadata for such facts, or avoid presenting unsupported generated-style details as verified.

Primary check: [HBO/Warner Bros. Discovery release](https://press.wbd.com/na/media-release/hbo-max/daniel-zovatto-and-lori-petty-star-max-original-station-eleven).

One surprising result was checked and **not** counted as a defect: Arlo Parks' directing credit for Knotted Gold is corroborated by [Gucci's own project page](https://www.gucci.com/lu/en_gb/st/stories/article/absolute-beginners-part-two) and [co-director Tom Dream](https://tomdream.co.uk/dazed-x-gucci-knotted-gold/). Unexpected does not mean incorrect.

### Lower-priority UI/coverage issues

- Twelve no-image fallbacks across the final ten-entity set, including all four On brand connections. No failed/pending cover elements in that sampled set after settling; this does not prove the new retry code was exercised by an actual failure.
- Bounded retry is implemented on canvas image elements; Gallery and other image surfaces do not share that handler. This is a source-review coverage gap, not a newly forced/live gallery failure.
- Profile/tag explanations remain weaker than a concrete statement of the shared subject. Looser results are explicitly labeled and must not be advertised as passing the strict gate.
- Long social actions remain disclosed starting-point-only; exact-copy links retain the map/descriptions.
- Fast confirmation fixture sometimes samples focus before animation-frame focus completes. Wait-aware3×8Tab/Escape control passes; no persistent nested-dialog focus escape established.

## Ten new intended entities

Stratified seed `2026102918`, concurrency two, fresh isolated contexts, no provider mocks. Provider-backed responses can use app/provider caches; this is not a claim of a fresh model judgement for every call.

Original results:9FLOW_PASS,1FAIL. The failed test was **On Running**, whose intended **On** brand and Swiss running-company description were already offered. The name-only harness did not recognize the alias. A separate explicit alias control selected only name=On,type=brand,with Swiss/running identity evidence, and passed the complete flow. No provider response was modified.

| Query | Final reviewed flow | Cards | Loaded art | Edges |
| --- | --- | ---: | ---: | ---: |
| Arlo Parks | Pass;classification issue above | 5 | 3 | 5 |
| Yo La Tengo | Pass | 5 | 5 | 5 |
| Alex Garland | Pass | 5 | 5 | 5 |
| Samanta Schweblin | Pass | 5 | 1 | 5 |
| On Running → On | Alias-aware recheck passed | 4 | 0 | 4 |
| The Green Knight | Pass | 3 | 3 | 3 |
| Exhalation | Pass | 3 | 3 | 3 |
| A Short Hike | Pass;includes looser results | 3 | 1 | 3 |
| The Leftovers | Pass;provider description issue above | 3 | 3 | 3 |
| Oslo, Norway | Pass | 5 | 5 | 5 |
| **Total including alias control** | **10intended entities explored** | **41** | **29** | **41** |

Original nine completed maps:37cards,29loaded covers,37edges. Adding the four-card alias control yields41cards/29covers/41edges,12no-image fallbacks,zero failed/pending image elements. Do not misreport the original runner as10automatic passes or these totals as an accuracy percentage.

## Geographic/identity regression controls

- Québec City now resolves to municipality ID `552E3F97-FC52-42CE-8E12-BED0076C206C`, returning Château Frontenac,Quartier Petit Champlain,Videotron Centre,Aquarium of Quebec,and Festival d'été office—not the previous Montréal mix.
- Berlin city returns East Side Gallery,Brandenburg Gate,Checkpoint Charlie,etc. No missing-city claim is made solely from a theoretical admin-level threshold.
- Edinburgh city and the Scotland ID at depths1and2 return the Scottish venues.
- Ontario/British Columbia and Île-de-France/Bordeaux helper controls both correctly reject conflicting regions.
- Freitag brand returns explicit type_missing and a similarly named flagship store. No claim of complete provider-database coverage.

## Saving, exploration and local retrieval

- The Lighthouse/Dark:save→unsave→save,reload,no Save-driven expansion,Gallery exploration hidden all pass.
- Resuming The Lighthouse sends one map-local positive signal;other-map positives absent from retrieved anchors.
- Actual agent3→8cards,streamed/reported five additions.
- Rejected I'm Thinking of Ending Things absent after reload and agent;present in dislikes/excludeIds,not positive memory. Map3→2after rejection,then→7after exploration.
- Not an exhaustive simultaneous-tab/alias/edition audit. No independent population JEV precision/recall study this round.

## Security, server and UI evidence

- Fourteen bounded exposure/body/origin checks passed:sensitive files404,unsupported GET405,null bodies400,foreign Origin403,oversized JSON400.
- Shared HTML/event handlers did not execute;javascript links and HTTP metadata-address images dropped. Not comprehensive penetration testing.
- Exact current runtime provider-key scan:two values,39public files,zero skipped,zero matches. No credentials printed. Does not audit private logs/history or establish rotation.
- Installed runtime137package names:zero advisories returned by npm registry bulk endpoint. Not proof of no vulnerabilities.
- Image `2026-10-29-33b4630`,healthy,user=node,read-only rootfs,app port unpublished. Secretfile600/root,Caddy logs10MB×3. Disk74%used,2.2GiBfree;watch headroom during repeated builds/deployments. Other EC2s untouched.
- Real filesystem contention:400allowed,200capped,zero busy,ledger400. No provider calls;crash/stale-lock cases not exhausted.
- Lint and48individual unit tests pass. Music type consistency is an additional failing observation not covered by those assertions.
- Modal/Share focus containment,exact description preservation,Wikidata badge,Gallery focus restoration,44×44Recents close pass. Wait-aware nested dialog3×8Tabs passes.
- Home reachability/no-overflow320×568,390×844,768×1024,1440×900,844×390;map widths320/390/768/1440 pass. Not full accessibility conformance.

## Evidence/reproduction

- `tests/live_queries_round18.py`; `/tmp/throughline-round18-results.json`.
- `tests/live_alias_control_round18.py`; `/tmp/throughline-round18-on-alias.json`.
- `tests/live_city_controls_round18.py`; `/tmp/throughline-round18-city-controls.json`.
- `tests/live_music_type_round18.py` (real initial/restored type inconsistency).
- Existing feedback/UI/security/geography/sanitization runners rerun;their `/tmp` outputs refreshed.
- Sanitized server/runtime-scan command `1b8fa027-1e53-47d9-aaed-ab85d40b2209`.

No new public credential exposure established in the tested scope. Key rotation remains unverified. No implementation or production changes in this review.
