#!/bin/sh
set -eu

if [ -z "${TS_AUTHKEY:-}" ]; then
  echo "ERROR: TS_AUTHKEY missing"
  exit 1
fi

tailscaled --tun=userspace-networking --socks5-server=127.0.0.1:1055 --state=mem: &

echo "Waiting for Tailscale daemon..."
ready=0
for i in $(seq 1 30); do
  if tailscale status --json >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done

if [ "$ready" -ne 1 ]; then
  echo "ERROR: Tailscale daemon not ready"
  exit 1
fi

tailscale up --authkey="$TS_AUTHKEY" --advertise-tags=tag:converter --hostname=migration-render-converter --accept-dns=false

exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-10000}"




