#!/bin/sh
# Arranque de Reset Gym en Render: API de Node en 127.0.0.1:3000 y nginx en el puerto de Render.
set -eu

export DATA_DIR="${DATA_DIR:-/data}"
mkdir -p "$DATA_DIR"
# Render pone la URL pública del servicio; las passkeys y las cookies se atan a ella.
export ORIGIN="${ORIGIN:-${RENDER_EXTERNAL_URL:-http://localhost:${PORT:-10000}}}"
export RP_ID="${RP_ID:-${RENDER_EXTERNAL_HOSTNAME:-localhost}}"
# El nombre que muestran las passkeys: el del gimnasio, si el servidor tiene marca propia.
export RP_NAME="${RP_NAME:-${GYM_NAME:-Reset Gym}}"
export TRUST_PROXY="${TRUST_PROXY:-1}"

PUBLIC_PORT="${PORT:-10000}"
API_PORT=3000

NGINX_PORT="$PUBLIC_PORT" BACKEND=127.0.0.1 PORT="$API_PORT" RESOLVER=1.1.1.1 \
CF_CONNECTING_IP="" BASE_PATH="" MEDIA_UPLOAD_MAX=48m \
  envsubst '${NGINX_PORT} ${BACKEND} ${PORT} ${RESOLVER} ${CF_CONNECTING_IP} ${BASE_PATH} ${MEDIA_UPLOAD_MAX}' \
  < /etc/nginx/reset-gym.conf.template > /etc/nginx/http.d/default.conf
# Las animaciones de ejercicios llevan Cross-Origin-Resource-Policy: same-origin para que otros
# sitios no las usen. La app de Android corre en https://localhost (su WebView) y quedaba fuera,
# así que aquí se deja pasar solo a la app: por su Origin (fetch) o su Referer (<img>, <video>).
# Cualquier otro sitio sigue recibiendo same-origin, y el CORS solo se abre para la app.
cat > /etc/nginx/http.d/00-reset-gym-maps.conf <<'MAPS'
map $http_origin $rg_acao {
    default "";
    "https://localhost" $http_origin;
    "capacitor://localhost" $http_origin;
    "http://localhost" $http_origin;
}
map "$http_referer|$http_origin" $rg_corp {
    default "same-origin";
    "~^(https|capacitor|http)://localhost(/[^|]*)?\|" "cross-origin";
    "~\|(https|capacitor|http)://localhost$" "cross-origin";
}
MAPS
sed -i 's#add_header Cross-Origin-Resource-Policy "same-origin" always;#add_header Cross-Origin-Resource-Policy $rg_corp always; add_header Access-Control-Allow-Origin $rg_acao always; add_header Vary "Origin, Referer" always;#' \
  /etc/nginx/http.d/default.conf
# Marca del gimnasio (nombre, logo, color) en la app web, si este servidor la tiene (RESET_GYM.md).
HTML_DIR=/usr/share/nginx/html node /app/render-brand.mjs || echo "Marca: no se pudo aplicar, se queda Reset Gym"

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
