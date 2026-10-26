# Reset Gym en Render: la app web y la API en UN solo servicio (Render da un puerto público por
# servicio). nginx sirve la app y pasa /api a la API de Node, que escucha dentro en el 3000.
# Los datos (cuentas, entrenamientos) van en /data: en Render eso es un disco persistente.

FROM node:22-alpine AS build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts
COPY api/coach/core/ /app/api/coach/core/
COPY frontend/ ./
RUN npm run build

FROM node:22-alpine
RUN apk upgrade --no-cache && apk add --no-cache nginx gettext
WORKDIR /app
COPY api/package.json api/package-lock.json ./
RUN npm ci --omit=dev --omit=optional && npm cache clean --force
COPY api/ ./
RUN adduser -D -H -s /sbin/nologin coach 2>/dev/null || true
COPY web/nginx.conf.template /etc/nginx/reset-gym.conf.template
COPY --from=build /app/frontend/dist /usr/share/nginx/html
# Animaciones de ejercicios (180 px, Gym visual, ver NOTICE.md): van dentro de la imagen.
COPY catalogue/media/ /usr/share/nginx/html/exercise-media/
COPY render/brand.mjs /app/render-brand.mjs
COPY --chmod=755 render/start.sh /start.sh
ENV NODE_ENV=production
CMD ["/start.sh"]
