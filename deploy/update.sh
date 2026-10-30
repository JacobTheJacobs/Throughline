#!/bin/sh
# Run on the dedicated Throughline instance after uploading Caddyfile.next.
set -eu
image=${1:?Pass the immutable ECR image tag}
case "$image" in 906969953480.dkr.ecr.eu-north-1.amazonaws.com/sideways:*) ;; *) exit 2 ;; esac
if docker inspect sideways-previous >/dev/null 2>&1; then
  test "$(docker inspect sideways-previous --format '{{.State.Running}}')" = false
  docker rename sideways-previous "sideways-previous-$(date +%s)"
fi
# Keep only the two newest archived rollback containers on the small volume.
docker ps -a --filter name=sideways-previous- --format '{{.Names}}' | sort -r | tail -n +3 | xargs -r docker rm
docker pull "$image"
docker run --rm --volume /opt/sideways/Caddyfile.next:/etc/caddy/Caddyfile:ro caddy:2.10-alpine caddy validate --config /etc/caddy/Caddyfile
# Service-wide API budget survives restarts here (uid 1000 = node in the image).
mkdir -p /opt/sideways/state && chown 1000:1000 /opt/sideways/state && chmod 700 /opt/sideways/state
docker run --detach --name sideways-candidate --restart unless-stopped \
  --network sideways --env-file /opt/sideways/app.env --env TRUST_PROXY_HEADERS=1 \
  --env GUARD_STATE_FILE=/state/guard.json --volume /opt/sideways/state:/state:rw \
  --read-only --tmpfs /tmp:rw,nosuid,size=64m --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 128 \
  --memory 640m --memory-swap 896m \
  --health-cmd 'node -e "fetch(\"http://127.0.0.1:8000/\").then(r=>process.exit(r.ok?0:1),()=>process.exit(1))"' \
  --health-interval 30s --health-timeout 10s --health-retries 3 --health-start-period 30s \
  --log-opt max-size=10m --log-opt max-file=3 "$image"
# The old service keeps serving until the new process passes its local check.
if ! docker exec sideways-candidate node --input-type=module -e 'for(let i=0;i<30;i++){try{const r=await fetch("http://127.0.0.1:8000/");if(r.ok)process.exit(0)}catch{}await new Promise(r=>setTimeout(r,1000))}process.exit(1)'; then
  docker rm -f sideways-candidate
  exit 1
fi
cp /opt/sideways/Caddyfile /opt/sideways/Caddyfile.previous
# Armed before the first cutover step: any failure from here restores the old service.
stopped=0
rollback(){
  trap - EXIT
  docker rm -f sideways-candidate >/dev/null 2>&1 || true
  if [ "$stopped" = 1 ]; then
    if docker inspect sideways-previous >/dev/null 2>&1; then
      docker rm -f sideways-app >/dev/null 2>&1 || true
      docker rename sideways-previous sideways-app || true
    fi
    docker start sideways-app || true
  fi
  cp /opt/sideways/Caddyfile.previous /opt/sideways/Caddyfile || true
  docker exec sideways-caddy caddy reload --config /etc/caddy/Caddyfile || true
  exit 1
}
trap rollback EXIT
stopped=1
docker stop --time 20 sideways-app
docker rename sideways-app sideways-previous
docker rename sideways-candidate sideways-app
# Copy into the existing mounted inode so Caddy sees the updated policy.
cp /opt/sideways/Caddyfile.next /opt/sideways/Caddyfile
docker exec sideways-caddy caddy reload --config /etc/caddy/Caddyfile
curl --fail --silent --show-error --retry 5 --retry-delay 1 --retry-all-errors --max-time 15 --output /dev/null https://throughline.51-21-210-47.sslip.io/
trap - EXIT
# Keep the stopped previous container for an explicit rollback after verification.
# Bound disk use: drop images no container (running or rollback) references, and builder cache.
docker image prune -af >/dev/null 2>&1 || true
docker builder prune -af >/dev/null 2>&1 || true
docker ps --filter name=sideways --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
