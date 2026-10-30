#!/bin/sh
# Dedicated Throughline host only. Preserve certificate/configuration bind mounts.
set -eu
name=sideways-caddy
backup=sideways-caddy-before-log-rotation
if docker inspect "$backup" >/dev/null 2>&1; then
  echo 'Existing rollback container found; inspect it before proceeding.' >&2
  exit 1
fi
options=$(docker inspect "$name" --format '{{json .HostConfig.LogConfig}}')
case "$options" in *'"max-size":"10m"'*'"max-file":"3"'*|*'"max-file":"3"'*'"max-size":"10m"'*) echo 'Rotation already configured.'; exit 0;; esac
image=$(docker inspect "$name" --format '{{.Image}}')
docker exec "$name" caddy validate --config /etc/caddy/Caddyfile
renamed=0
rollback(){
  trap - EXIT
  if [ "$renamed" = 1 ]; then
    docker rm -f "$name" >/dev/null 2>&1 || true
    docker rename "$backup" "$name" || true
  fi
  docker start "$name" >/dev/null || true
  echo 'Rotation failed; original Caddy restart attempted.' >&2
  exit 1
}
trap rollback EXIT
docker stop --time 10 "$name" >/dev/null
docker rename "$name" "$backup"
renamed=1
docker run --detach --name "$name" --restart unless-stopped \
  --network sideways --publish 80:80 --publish 443:443 --publish 443:443/udp \
  --volume /opt/sideways/Caddyfile:/etc/caddy/Caddyfile:ro \
  --volume /opt/sideways/caddy-data:/data \
  --volume /opt/sideways/caddy-config:/config \
  --log-driver json-file --log-opt max-size=10m --log-opt max-file=3 "$image" >/dev/null
curl --fail --silent --show-error --retry 8 --retry-delay 1 --retry-all-errors \
  --max-time 10 --output /dev/null \
  --resolve throughline.51-21-210-47.sslip.io:443:127.0.0.1 \
  https://throughline.51-21-210-47.sslip.io/
trap - EXIT
docker inspect "$name" --format 'running={{.State.Running}} logs={{json .HostConfig.LogConfig}}'
echo 'Original stopped container retained as sideways-caddy-before-log-rotation.'
