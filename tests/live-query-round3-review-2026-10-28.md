# Third live discovery audit — 28 October 2026

Reviewed application commit: `46e99de` (Identity coverage, feedback consistency, recent-map actions).

## Outcome

Ten new, reproducibly sampled queries: **9 initial browser-flow passes, 1 failure**. Follow-up tests found substantive identity and feedback defects despite the improvements in the last commit. This is not an all-clear.

This pass changes only tests and this report. It does not implement application fixes or change relevance thresholds.

## Findings

### 1. High — category-word parsing corrupts literal work titles

`splitTypedQuery` unconditionally strips trailing words such as Book, Movie and Artist before searching. These words can be part of a title, not a user's category instruction.

Real live discovery endpoint results:

- **The Jungle Book** becomes **The Jungle**. The returned seed is book `54327B87-7EDE-4CB4-9062-B68D5D36D72D`, with a description about a Lithuanian immigrant and Chicago's meat industry. It then reports no relevant matches for that different reference.
- **The Artist** becomes **The**, resolving to artist `F2315E89-87F4-43E2-A937-BBECB1F4E1FD` and offering the creator intent for The.
- **Scary Movie** asks which Scary the user meant and mixes unrelated categories. The correct 2000 film remains offered, so this example adds avoidable ambiguity rather than making the film entirely unreachable.

Code: [parser](../app/api/discover/route.ts#L18), [parsed query and preferred type](../app/api/discover/route.ts#L163).

Required correction: preserve and resolve literal titles first. Apply category suffix interpretation only with evidence or explicit syntax. Do not let a guess about query syntax override a valid exact title.

### 2. High — geographic identity coverage still fails for Iceland

The new randomized browser test for **Iceland** offers places and an album, not the country. Adding country does not recover it: **Iceland country** offers hotels, restaurants, a country-music museum and other unrelated places.

A separate read-only provider lookup proves the country record exists:

```
query=Iceland, types=urn:entity:locality
id: 960EA243-A1EF-4826-BCE4-378AF592E370
name: Ísland
Wikidata: Q189
```

The recovery lookup for crowded same-name places currently searches only brands. The typed-word parser also does not recognize country/city intent. The localized name Ísland requires identity/alias-aware handling; accent stripping alone does not turn it into Iceland.

Code: [type words](../app/api/discover/route.ts#L17), [brand-only crowd-out lookup](../app/api/discover/route.ts#L179).

Required correction: bounded category-aware identity recovery, including geographic aliases and locality records. Do not invent a boundary or automatically choose an individual store.

### 3. High — cross-provider aliases bypass novelty, saving and rejection consistency

This was reproduced through the visible browser interface, not just an API request:

1. Search Octavia E. Butler and choose the identified writer.
2. Save **Parable of the Talents**, displayed with ID `wikidata:Q3211325`.
3. Open **Parable of the Sower** and choose Books.
4. The map grows from five to six nodes, adding **Parable of the Talents (Earthseed, #2)** with Qloo ID `7DEDF979-7343-4B8D-BD58-D335F6B24D92`.
5. Reject that Qloo copy. The original remains saved, with Saved 1.

The subsequent category request includes both contradictory signals, and graph-memory retrieval explicitly says:

```
Strong signals: Parable of the Talents (book).
Avoid: Parable of the Talents (Earthseed, #2).
```

This is one work under two provider IDs, not a legitimate distinct adaptation. `placeBatch`, exclusion lists, feedback state and graph-memory keys all use literal provider IDs. The new crosswalk resolves an input anchor but does not establish a shared canonical identity for the other works already displayed or rated.

Code: [crosswalk](../app/api/discover/route.ts#L168), [ID-only insertion](../app/page.tsx#L67), [save/reject operations](../app/page.tsx#L199), [memory latest-feedback keys](../lib/feedback.ts#L3), [memory retrieval](../lib/taste-memory.ts#L35).

Required correction: persist verified alias-to-canonical mappings and apply them consistently to insertion, exclusions, saved state, feedback, memory and provenance. Do not merge unrelated same-title works by title alone.

### 4. Medium — the agent exhausts its budget while missing a verified available adaptation

On the Murakami map with Norwegian Wood saved, the agent now correctly scores all five displayed books. The previous bug that excluded every Wikidata-only anchor is fixed.

However, this live run added **zero** recommendations. Its stream tried artists/places from Norwegian Wood and similarly speculative categories from other books, then ended with Search limit reached. It never tried Movies for Norwegian Wood.

A follow-up live category request using the same source ID and map exclusions immediately returns the 2010 **Norwegian Wood** film, with a verified Adapted from Norwegian Wood relationship and `availability.movie=available`.

The agent chooses at most two target categories per parent from prediction scores. It does not first use factual connection availability or reuse the inspector's final availability answers. It can therefore spend its nine-request branch budget without trying a directly supported continuation.

Code: [target prediction](../app/api/agent/route.ts#L98), [two-target cutoff](../app/api/agent/route.ts#L104), [branch budget](../app/api/agent/route.ts#L75).

Required correction: prefer known available/verified continuations before speculative cross-domain branches. Keep the budget and relevance gate; do not force five weak results to hide this recall problem. This is evidence of a missed opportunity in this run, not a claim that every agent run must always find five results.

### 5. Medium — a source-backed credit is shown as unqualified verified fact despite conflicting official credits

Greta Gerwig's live initial map includes **Snow White (2025)** labeled Screenplay by Greta Gerwig and Verified direct relationship.

[Disney's official film page](https://movies.disney.com/snow-white-2025) lists Erin Cressida Wilson as the writer; its [final production notes](https://lumiere-a.akamaihd.net/v1/documents/disney_s_snow_white_final_production_notes_and_bios_1cd49638.pdf) also attribute the screenplay to Wilson. This does not establish that Gerwig never worked on a draft. It does establish that the application's unqualified final-credit wording is not reconciled with the official released-film attribution.

The direct-credit query reads Wikidata's simplified truthy properties and does not retain statement references, dates, qualifiers or credit status. A database relationship being present is not equivalent to independent verification of current released-screen credits.

Code: [simplified credit query](../app/api/discover/route.ts#L91), [generic verified-credit output](../app/api/discover/route.ts#L269).

Required correction: retain source and credit status, qualify draft/uncredited/disputed contributions where supported, and resolve conflicts against an authoritative credit source. Avoid presenting every imported statement as independently verified fact.

## Ten new randomized queries

Sampling seed: `2026102803`. One new query was sampled from each category pool before requests began; failures were not replaced. Browser contexts were fresh and isolated, with 1440px desktop and 390px mobile checks. Real local application and configured providers were used, without API mocks.

| Query | Initial flow | Cards | Examples / observation |
| --- | --- | ---: | --- |
| Greta Gerwig | Pass | 5 | Barbie, Lady Bird, Little Women, Frances Ha, Snow White. See credit caveat above. |
| Octavia E. Butler | Pass | 5 | Parable of the Sower, Kindred, Lilith's Brood, Survivor, Parable of the Talents. Alias feedback defect appears on expansion. |
| Daft Punk | Pass | 5 | Tron: Legacy, Interstella 5555, Random Access Memories, Get Lucky, Discovery; musical work types retained. |
| Uniqlo | Pass | 1 | Tadashi Yanai, factual founder relationship. No invented padding. |
| Everything Everywhere All at Once | Pass | 4 | Mitski, Barbie, Across the Spider-Verse, Multiverse of Madness. |
| Neuromancer | Pass | 1 | Count Zero. Source selection includes 1984 publication metadata; the provider excerpt is German. |
| Elden Ring | Pass | 2 | Bloodborne, Demon's Souls. Source selection includes 2022 release metadata. |
| The Bear | Pass | 3 | Somebody Somewhere, Shrinking, Hacks. Source selection includes 2022 release metadata. |
| The Moth | Pass | 1 | RISK! |
| Iceland | **Fail** | — | Country missing from chooser despite existing in provider. |

A flow pass checks unique non-source card count, source context, relationship explanations, opening a card, save without graph expansion/discovery requests, persistence after reload without a repeated search, Gallery navigation and horizontal overflow. It is not proof of factual correctness of every description, rating, credit or suggested connection. Year/description expectations were checked where clarification choices exposed them; an automatically resolved query is not claimed to have passed an unseen year check.

No application JavaScript errors or HTTP-error warnings were recorded in the nine passing initial flows. The harness now counts request starts rather than response completions when checking whether Save causes an extra request, avoiding a false failure from an already-running request finishing later.

## Live JEV semantic-gate check on new evidence

Eight new labeled pairs, two fresh-cache runs each. Canonical anchor descriptions came from a live provider entity read; candidates came from this round's returned data. Affinity was fixed at 0.95 to isolate semantic qualification. Crossed negative pairs are **not** claimed to have been actual Qloo recommendations.

| Anchor → candidate | Expected | Live votes |
| --- | --- | --- |
| Elden Ring → Bloodborne | Keep | Keep / Keep |
| Elden Ring → RISK! | Reject | Reject / Reject |
| Neuromancer → Count Zero | Keep | Keep / Keep |
| Neuromancer → Barbie | Reject | Reject / Reject |
| The Moth → RISK! | Keep | Keep / Keep |
| The Moth → Bloodborne | Reject | Reject / Reject |
| Everything Everywhere All at Once → Mitski | Keep | Keep / Keep |
| Everything Everywhere All at Once → Uniqlo | Reject | Reject / Reject |

Result: 4 true-positive pairs, 4 true-negative pairs, zero misses, zero unstable pairs, zero failed calls. These are small, selected regression cases, not a population-wide accuracy estimate. They do not test identity resolution, factual credit verification, recall of unqueried categories or cross-provider feedback consistency—the layers where this audit reproduced failures.

## Confirmed improvements and other checks

- IKEA's brand is now offered first in the rechecked chooser.
- Le Guin's 1974 The Dispossessed is now offered first, with subtitle preserved.
- Norwegian Wood retains its Wikidata identity through category requests; the server crosswalks it to the Qloo book and no longer mistakes clarification for pending work.
- Murakami's agent run scores five works rather than silently filtering them all out. Its remaining zero-result failure is a target-selection issue, not the old pool filter.
- Actual category/agent requests carry map-scoped graph-memory context.
- The availability UI no longer claims ten confirmed matches in the Norwegian Wood empty-category case.
- Saving in all nine initial passing flows remains one saved card, does not grow the graph, and survives reload; Gallery opens without horizontal page overflow.
- Visible Home → new The Bear exploration in the same browser displays Saved 0 and sends no inherited liked/disliked IDs or positive/negative memory anchors. No cross-map save leakage was reproduced.
- Unit suite passed again. No production build was run because application code was not changed in this review.

## Artifacts and test limitations

Raw isolated-browser evidence: `/tmp/sideways-round3-review-evidence.json`; sampled query data: `/tmp/sideways-round3-queries.json`. No credentials are included.

Reproduction scripts: `tests/live_queries_round3.py`, `tests/live_alias_feedback.py`, `tests/live_round3_paths.py`, with the shared `tests/live_queries.py` harness.

An initial audit-observer setup error was corrected before collecting the useful Murakami stream. A later attempt to type into the intentionally hidden map-header input timed out; it is not counted as an application failure or a passed isolation check. Isolation was subsequently tested through the visible Home controls. The new scripts reflect that visible route.

The literal-title follow-ups and expected-adaptation check were real endpoint tests, not full browser completion tests for those extra queries. The duplicate/save/reject and map-isolation reproductions were full visible browser interactions. No claim is made that every query, every category, every future model decision or every external rating has been validated.
