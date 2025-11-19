# syntax=docker/dockerfile:1.7
FROM node:20-alpine AS build
WORKDIR /repo

# Install git (required by some pnpm dependencies)
RUN apk add --no-cache git

ENV COREPACK_ENABLE_DOWNLOADS=1
RUN corepack enable && corepack prepare pnpm@10.20.0 --activate

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN printf "store-dir=/pnpm\nshared-workspace-lockfile=true\n" > /etc/pnpmrc

COPY pkgs/js pkgs/js

# Install dependencies for workspace packages first
# This ensures all workspace dependencies are resolved before installing app dependencies
# Using BuildKit cache mount for pnpm store (node_modules created as regular layer)
RUN --mount=type=cache,id=pnpm-store,target=/pnpm \
    PNPM_STORE_DIR=/pnpm \
    pnpm install --frozen-lockfile --filter "@quizbee/ui-svelte-daisy" --include-workspace-root=false
RUN --mount=type=cache,id=pnpm-store,target=/pnpm \
    PNPM_STORE_DIR=/pnpm \
    pnpm install --frozen-lockfile --filter "@quizbee/pb-types" --include-workspace-root=false


# Now install app dependencies with workspace packages available
COPY srvs/app/package.json srvs/app/
RUN --mount=type=cache,id=pnpm-store,target=/pnpm \
    PNPM_STORE_DIR=/pnpm \
    pnpm install --frozen-lockfile --filter ./srvs/app...

COPY srvs/app srvs/app

# Build args for SvelteKit env vars (PUBLIC_ prefix required by SvelteKit)
ARG STRIPE_API_KEY
ARG PUBLIC_PB_URL
ENV STRIPE_API_KEY=$STRIPE_API_KEY PUBLIC_PB_URL=$PUBLIC_PB_URL


RUN pnpm -C srvs/app build

RUN mkdir -p /out && \
    pnpm --filter ./srvs/app deploy --prod --legacy /out && \
    cp -r srvs/app/build /out/build

### 2) Runtime
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=build /out/ ./

EXPOSE 3000
CMD ["node", "build/index.js"]
