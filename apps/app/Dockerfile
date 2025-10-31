FROM node:20-alpine AS build
WORKDIR /repo

ENV COREPACK_ENABLE_DOWNLOADS=1
RUN corepack enable && corepack prepare pnpm@10.18.2 --activate
ENV PNPM_STORE_DIR=/pnpm
RUN mkdir -p /pnpm && chmod -R 777 /pnpm
RUN printf "store-dir=/pnpm\nshared-workspace-lockfile=true\n" > /etc/pnpmrc

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY pkgs/js/*/package.json pkgs/js/*/
COPY apps/app/package.json apps/app/

RUN pnpm install --frozen-lockfile --filter ./apps/app...

COPY pkgs/js pkgs/js
COPY apps/app apps/app

RUN pnpm -C apps/app build

RUN pnpm deploy --filter ./apps/app --prod --dir /out
RUN cp -r apps/app/build /out/build

### 2) Runtime
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=build /out/ ./

EXPOSE 3000
CMD ["node", "build/index.js"]
