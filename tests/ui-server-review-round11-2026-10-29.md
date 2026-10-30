# Throughline UI, security and server review — 2026-10-29

Scope: read-only production inspection, source review, production-browser tests using an explicitly synthetic shared-map fixture, and offline deployment failure injection. No application or production configuration was changed in this pass. This is not a penetration-test certification.

## Findings

1. **High — deployment can stop the service without rolling back.** `deploy/update.sh:24–26` stops the old container before an unchecked rename; `set -e` exits before the rollback function is defined. Offline failure injection against the actual script produced `script_exit=1`, `old_service_stopped=yes`, `rollback_restart=no`. The stubs did not operate on Docker or production. Install cleanup/error handling before the first state change and cover every cutover failure.
2. **High — paid APIs have no service-wide spending circuit breaker.** `lib/guard.ts:7–14,38–46` has process-local per-IP caps, not a durable aggregate provider budget. Distributed clients and process restarts defeat a total spending ceiling. This is an architectural cost-exposure finding, not a demonstrated attack. Add aggregate budgets and global concurrency bounds without weakening the existing per-request limits.
3. **Medium — social sharing silently loses the map.** `app/page.tsx:357` falls back to a seed-only URL at 1,800 characters while the dialog promises the complete graph. A 12-reference fixture generated a 4,477-character exact URL; social sharing retained only the seed. Exact sharing also omits descriptions (`app/page.tsx:353`). Use persisted snapshots or explicitly label the reduced link.
4. **Medium — share modal focus escapes.** On the live site, focus was not moved into the dialog and Tab from the last social action escaped it. `aria-modal` alone does not implement modal keyboard behavior. Gallery inspector close also failed to restore focus to its gallery opener (`app/page.tsx:224`). The nested removal confirmation passed its focus test.
5. **Medium — factual evidence is mislabeled as Qloo.** A synthetic verified Wikidata “Written by” reference displayed a Qloo badge in the brief (`app/page.tsx:421`). Render the actual evidence provider and relationship, not a Qloo fallback.
6. **Medium — weak recovery and bounded-storage coverage.** The production app has no Docker healthcheck; restart policy is `unless-stopped`, which does not detect a hung running process. No matching instance-dimension CloudWatch metric alarms were found in eu-north-1 (other monitoring was not ruled out). App logs are capped at 3×10 MB, but Caddy inspection shows no rotation options. Three stopped rollback containers were retained; the update script archives previous containers indefinitely on an 8 GiB volume. Add external health alerting/recovery, bounded logs and a rollback retention policy. A Docker healthcheck alone does not restart unhealthy containers.
7. **Low — mobile close control is small.** Recent explorations has a 30×30 px close button (`app/globals.css:966`). Increase its effective hit area; this observation alone is not a claimed WCAG failure.

## Security controls verified / boundaries

- Dedicated EC2 volume is encrypted gp3, 8 GiB; CPU credit mode is standard.
- Runtime secret file mode is 0600 owned by root. Values were not printed in this pass.
- App runs non-root with read-only root filesystem, dropped capabilities, no-new-privileges, memory/PID limits, and no published app port.
- Instance role has SSM core access, ECR read-only access and SSM parameter reads scoped to `/sideways/prod/*`. ECR read access could be narrowed to this application's repository.
- Previous round found no exact secret values in the scanned public assets and no known dependency vulnerabilities in the deployed audit. Those were previous-round checks, not a new exhaustive scan here.
- Rotation of Qloo/JEV keys previously exposed in private diagnostic output remains unverified. Rotate/revoke old keys; no public leak is established by this review.
- OS patch automation and external/composite monitoring were not fully audited. Do not infer their absence from the inspected timer/alarm subset.

## Reproduction

- `sh tests/deploy_review_round11.sh` — offline stubs only; reports rollback failure.
- `tests/live_ui_review_round11.py` — production browser, synthetic shared-map fixture; clipboard/social navigation intercepted. No provider responses mocked and no live-provider accuracy claim is made from this test.
- Browser evidence: share initial focus inside=false; share Tab wrap inside=false; exact URL length=4477; descriptions preserved=false; social preserves map=false; social uses seed only=true; factual badge=Qloo; nested confirmation focus inside=true; gallery focus restored=false; recents close=30×30 px.

## Primary guidance

- [WAI-ARIA modal dialog keyboard and focus behavior](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
- [Docker restart policy behavior](https://docs.docker.com/engine/containers/start-containers-automatically/)
- [Docker logging configuration and rotation](https://docs.docker.com/engine/logging/configure/)
- [EC2 shared security responsibilities](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security.html)
