# Imagen de producción de Next.js (output: "standalone" en next.config.ts)
FROM node:24-alpine AS dependencias
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

FROM node:24-alpine AS compilacion
WORKDIR /app
# Los rewrites de /api/v1 se resuelven al compilar: aquí se indica dónde está el backend
ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=$BACKEND_URL \
    NEXT_TELEMETRY_DISABLED=1
COPY --from=dependencias /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:24-alpine AS ejecucion
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0
RUN addgroup -S app && adduser -S app -G app
COPY --from=compilacion --chown=app:app /app/public ./public
COPY --from=compilacion --chown=app:app /app/.next/standalone ./
COPY --from=compilacion --chown=app:app /app/.next/static ./.next/static
USER app
EXPOSE 3000
CMD ["node", "server.js"]
