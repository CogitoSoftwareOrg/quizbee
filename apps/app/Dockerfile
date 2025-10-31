FROM node:20-alpine AS build
WORKDIR /repo

# Install git (required by some pnpm dependencies)
RUN apk add --no-cache git

ENV COREPACK_ENABLE_DOWNLOADS=1
RUN corepack enable && corepack prepare pnpm@10.18.2 --activate
ENV PNPM_STORE_DIR=/pnpm
RUN mkdir -p /pnpm && chmod -R 777 /pnpm
RUN printf "store-dir=/pnpm\nshared-workspace-lockfile=true\n" > /etc/pnpmrc

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY pkgs/js pkgs/js

# Build workspace packages BEFORE installing app dependencies
# This ensures symlinks point to compiled packages
RUN pnpm install --frozen-lockfile --filter ./pkgs/js/ui-svelte-daisy --include-workspace-root=false
RUN pnpm -C pkgs/js/ui-svelte-daisy build

# Now install app dependencies with compiled workspace packages available
COPY apps/app/package.json apps/app/
RUN pnpm install --frozen-lockfile --filter ./apps/app...

COPY apps/app apps/app

# Build args for SvelteKit env vars (PUBLIC_ prefix required by SvelteKit)
ARG PUBLIC_PB_URL=http://localhost:8090
ENV PUBLIC_PB_URL=$PUBLIC_PB_URL

RUN pnpm -C apps/app build

RUN mkdir -p /out
RUN pnpm --filter ./apps/app deploy --prod --legacy /out
RUN cp -r apps/app/build /out/build

### 2) Runtime
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=build /out/ ./

EXPOSE 3000
CMD ["node", "build/index.js"]
