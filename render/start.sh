#!/bin/sh
# Arranque de Reset Gym en Render: API de Node en 127.0.0.1:3000 y nginx en el puerto de Render.
set -eu

export DATA_DIR="${DATA_DIR:-/data}"
mkdir -p "$DATA_DIR"
# Render pone la URL pública del servicio; las passkeys y las cookies se atan a ella.
export ORIGIN="${ORIGIN:-${RENDER_EXTERNAL_URL:-http://localhost:${PORT:-10000}}}"
export RP_ID="${RP_ID:-${RENDER_EXTERNAL_HOSTNAME:-localhost}}"
export RP_NAME="${RP_NAME:-Reset Gym}"
export TRUST_PROXY="${TRUST_PROXY:-1}"

PUBLIC_PORT="${PORT:-10000}"
API_PORT=3000

NGINX_PORT="$PUBLIC_PORT" BACKEND=127.0.0.1 PORT="$API_PORT" RESOLVER=1.1.1.1 \
CF_CONNECTING_IP="" BASE_PATH="" MEDIA_UPLOAD_MAX=48m \
  envsubst '${NGINX_PORT} ${BACKEND} ${PORT} ${RESOLVER} ${CF_CONNECTING_IP} ${BASE_PATH} ${MEDIA_UPLOAD_MAX}' \
  < /etc/nginx/reset-gym.conf.template > /etc/nginx/http.d/default.conf
mkdir -p /run/nginx
nginx -t

PORT="$API_PORT" node /app/server.js &
API=$!
nginx -g 'daemon off;' &
WEB=$!
echo "Reset Gym: web en :$PUBLIC_PORT, API en :$API_PORT, origen $ORIGIN"

# Si cualquiera de los dos se cae, el contenedor termina y Render lo reinicia.
trap 'kill $API $WEB 2>/dev/null' TERM INT
while kill -0 "$API" 2>/dev/null && kill -0 "$WEB" 2>/dev/null; do sleep 5; done
kill "$API" "$WEB" 2>/dev/null || true
exit 1
