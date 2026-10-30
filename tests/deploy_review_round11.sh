#!/bin/sh
# Offline failure injection against the actual deployment script.
set -u
cd "$(dirname "$0")/.." || exit 1
review_tmp=$(mktemp -d /tmp/throughline-deploy-review.XXXXXX)
export DEPLOY_AUDIT_LOG="$review_tmp/commands.log"
PATH="$PWD/tests/fixtures/deploy-review-bin:$PATH" sh deploy/update.sh 906969953480.dkr.ecr.eu-north-1.amazonaws.com/sideways:review-fixture
result=$?
printf 'script_exit=%s\n' "$result"
if grep -q 'docker stop --time 20 sideways-app' "$DEPLOY_AUDIT_LOG"; then printf 'old_service_stopped=yes\n'; fi
if grep -q 'docker start sideways-app' "$DEPLOY_AUDIT_LOG"; then printf 'rollback_restart=yes\n'; else printf 'rollback_restart=no\n'; fi
printf 'stub_log=%s\n' "$DEPLOY_AUDIT_LOG"
