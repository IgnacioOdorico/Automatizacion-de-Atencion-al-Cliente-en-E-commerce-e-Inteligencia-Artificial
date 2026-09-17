# ============================================================
#  dashboard-web — Portal del cliente (React Vite + TS + nginx)
#  Multi-stage:
#    stage 1: node:22-alpine -> vite build -> dist/
#    stage 2: nginx:alpine     -> sirve dist/ + proxy /api -> dashboard-api:8000
# ============================================================

FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]