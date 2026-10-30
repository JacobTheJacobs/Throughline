# Sideways submission brief

## One-line pitch

Sideways is a Qloo-powered cultural research agent that turns one trusted reference into an explainable, cross-domain creative territory and a shareable taste brief.

## The user and the problem

Sideways is for brand strategists, designers, filmmakers, writers, and creative directors. Their research is scattered across search, moodboards, streaming catalogs, social platforms, and travel sites; the connections are manual and the reasoning gets lost. Sideways answers: “Which cross-domain references belong in this creative territory, why do they belong, and how can I take the result into my work?”

## Why it is agentic

The agent does not merely format one API response. It:

1. reads the complete visible taste map and local feedback memory;
2. uses JEV to rank which branches deserve growth;
3. selects a cross-domain direction for each branch;
4. queries Qloo for real affinity-ranked entities;
5. critiques candidates against positive and negative taste evidence;
6. adds only candidates that pass the match threshold;
7. records the causal edge and outcome for later retrieval.

Qloo owns entity truth and cultural affinity. JEV owns planning and critique. Sideways owns graph state, deduplication, interaction memory, and explanation. No model invents entities to fill the canvas.

## Why the graph is functional

Every edge records a source entity, destination entity, Qloo affinity, requested category, reason, session, and user outcome. Hovering or selecting a card isolates the causal path back to the seed. Graph mode answers “How did I get here?” Arrange mode answers “What did I find?”

## Judge demo

Use the six-step path in the README. Keep the demo under three minutes. Start clean with Spirited Away, save references from at least three categories, reject one weak match, run the goal-aware agent once, and finish by copying the generated taste brief. The outcome—not the number of nodes—is the payoff.

## Evidence to collect before submitting

Do not fabricate these numbers. Test with 10–20 people and report:

- percentage who saved an unfamiliar cross-category discovery within three minutes;
- median discoveries saved;
- relevance rating (1–5);
- surprise rating (1–5);
- percentage who correctly explained why one result appeared;
- failed searches, confusing controls, and observed recovery rate.

Comparative task: “Starting with Spirited Away, find five references across at least three categories that could inspire a campaign about nostalgic wonder.” Compare Sideways with each participant's normal Google or generic-chat workflow. Measure time, category diversity, relevance, surprise, explanation accuracy, and willingness to use the resulting brief. Publish only results actually collected.

## Required submission gates

- [ ] Add a public, fully published demo URL to README and Devpost.
- [ ] Confirm the public repository and MIT license are visible.
- [ ] Use the same product name—Sideways—on Devpost, the repository, video, and demo.
- [ ] Record a short video showing Qloo data, agent decisions, path explanation, feedback, Arrange, and History.
- [ ] Run `npm run lint`, `npm run test:unit`, `npm run build`, `npm run test:ui`, and `npm run test:judge` against the production candidate.
- [ ] Test Qloo unavailable, empty results, ambiguous seeds, reduced motion, keyboard use, mobile width, and refresh recovery.
- [ ] Remove secrets, sample personal data, and development-only URLs from the submission.

## Honest limitations

- Browser-local Taste GraphRAG is intentionally private and demo-friendly; it does not sync between devices.
- The in-process rate limiter is suitable for a hackathon demo, not a distributed production deployment.
- Recommendation quality depends on Qloo coverage and the quality of the starting entity.
- The current validation metrics must come from real participants before they can be presented as impact evidence.

## Expansion story

The same explainable navigation engine can support creative research, editorial development, travel inspiration, brand audience exploration, and cultural strategy. These are expansion markets, not claims that the current demo already solves every workflow.
