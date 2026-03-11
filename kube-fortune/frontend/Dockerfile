# ════════════════════════════════════════
# Stage 1 — Node.js 빌드 (arm64 호환)
# ════════════════════════════════════════
FROM node:20-slim AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

# ════════════════════════════════════════
# Stage 2 — Nginx 서빙 (arm64 호환)
# K8s 프로덕션: nginx.conf 사용
# 로컬 테스트:  docker-compose.yml에서 nginx.local.conf를 볼륨 마운트로 덮어씀
# ════════════════════════════════════════
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# K8s 프로덕션용 설정 기본 탑재
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
