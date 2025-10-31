FROM node:20-alpine AS build
WORKDIR /repo

ARG PUBLIC_APP_URL
ARG PUBLIC_PB_URL
ARG PB_URL
ARG PB_EMAIL
ARG PB_PASSWORD

ENV PUBLIC_APP_URL=$PUBLIC_APP_URL
ENV PUBLIC_PB_URL=$PUBLIC_PB_URL
ENV PB_URL=$PB_URL
ENV PB_EMAIL=$PB_EMAIL
ENV PB_PASSWORD=$PB_PASSWORD

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

# Install dependencies for ui-astro so it can resolve ui-svelte-daisy
RUN pnpm install --frozen-lockfile --filter ./pkgs/js/ui-astro --include-workspace-root=false

# Now install app dependencies with compiled workspace packages available
COPY apps/web/package.json apps/web/
RUN pnpm install --frozen-lockfile --filter ./apps/web...

COPY apps/web apps/web

RUN pnpm -C apps/web build

RUN mkdir -p /out
RUN pnpm --filter ./apps/web deploy --prod --legacy /out
RUN cp -r apps/web/dist /out/dist

### 2) Runtime
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=build /out/ ./

EXPOSE 3000
ENV HOST=0.0.0.0 PORT=3000
CMD ["node", "dist/server/entry.mjs"]
