FROM node:20-alpine AS build
WORKDIR /repo

ENV COREPACK_ENABLE_DOWNLOADS=1
RUN corepack enable && corepack prepare pnpm@10.18.2 --activate
ENV PNPM_STORE_DIR=/pnpm
RUN mkdir -p /pnpm && chmod -R 777 /pnpm
RUN printf "store-dir=/pnpm\nshared-workspace-lockfile=true\n" > /etc/pnpmrc

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY pkgs/js/*/package.json pkgs/js/*/
COPY apps/web/package.json apps/web/
RUN pnpm install --frozen-lockfile --filter ./apps/web...

COPY pkgs/js pkgs/js
COPY apps/web apps/web

RUN pnpm -C apps/web build

RUN pnpm deploy --filter ./apps/web --prod --dir /out
RUN cp -r apps/web/dist /out/dist

### 2) Runtime
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=build /out/ ./

EXPOSE 3000
CMD ["node", "dist/server/entry.mjs"]
