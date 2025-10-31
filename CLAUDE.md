# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QuizBee is a full-stack AI-powered quiz generation platform with three main applications:

- **API** (Python FastAPI) - Backend services and AI quiz generation
- **Web** (Astro) - Marketing website and landing pages
- **App** (SvelteKit SPA + Capacitor) - Interactive quiz application

## Development Setup

### Starting Development Environment

```bash
# Start all services (infra + dev servers)
make dev
```

This command:

1. Starts Docker infrastructure (PocketBase, Meilisearch, Dragonfly)
2. Starts API on port 8000 (FastAPI with auto-reload)
3. Starts web on port 4321 (Astro)
4. Starts app on port 5173 (SvelteKit/Vite)

All processes run in background with logs in `./logs/` and PIDs in `.pids/`

### Common Commands

```bash
# Infrastructure
make up              # Start Docker services only
make down            # Stop Docker services
make status          # Check running services

# Process management
make stop            # Stop all dev processes
make logs            # Tail all logs
make tail LOG=api    # Tail specific log (api|web|app|compose)
make clean           # Remove logs and PIDs

# Pull requests
make pr              # Create draft PR to main
```

### API Development

```bash
cd apps/api

# Run API server
make dev             # Start with auto-reload on 0.0.0.0:8000
make debug           # Start with debug logging

# Stripe webhook testing
make stripe          # Forward webhooks to localhost:8000

# Python environment (uses uv)
uv sync              # Install dependencies
uv run pytest        # Run tests
```

### Web Development

```bash
cd apps/web

pnpm astro dev       # Start dev server
pnpm build           # Build for production
pnpm preview         # Preview production build

# Generate PocketBase types
pnpm build:gen-types
```

### App Development

```bash
cd apps/app

pnpm dev             # Start dev server
pnpm build           # Build for production
pnpm preview         # Preview production build

# Code quality
pnpm check           # Type check with svelte-check
pnpm check:watch     # Watch mode type checking
pnpm lint            # Run ESLint + Prettier
pnpm format          # Format with Prettier

# Testing
pnpm test:unit       # Run Vitest unit tests
pnpm test:e2e        # Run Playwright E2E tests
pnpm test            # Run all tests

# Generate PocketBase types
pnpm build:gen-types
```

## Architecture

### Backend (API)

**Location:** `apps/api/src/`

**Structure:**

- `bootstrap/` - FastAPI application initialization and middleware setup
- `lib/` - Shared utilities and core services
  - `clients/` - External service clients (PocketBase, Meilisearch, Redis)
  - `config/` - Configuration management (LLM, billing, logging)
  - `ai/` - AI/LLM integration utilities
  - `models/` - Pydantic models and schemas
  - `utils/` - Utility functions
- `apps/` - Domain-driven feature modules (v2 architecture)
  - `edge_api/` - Public API endpoints for frontend (v2 refactored API)
  - `v2/` - New architecture modules (llm_tools, material_search, user_auth)
  - `quiz_generator/`, `quiz_attempter/`, `quiz_attempts/` - Quiz business logic
  - `materials/`, `messages/`, `billing/` - Supporting features

**Key Dependencies:**

- FastAPI + Uvicorn for HTTP
- Pydantic-AI for LLM orchestration
- PocketBase (async) for database
- Meilisearch for search
- Dragonfly (Redis-compatible) for caching
- ARQ for background jobs
- Stripe for billing

**Entry Point:** `src/bootstrap:app` (FastAPI app instance)

### Frontend (App)

**Location:** `apps/app/src/`

**Structure:**

- `routes/` - SvelteKit file-based routing
  - `(user)/` - Protected user routes (requires auth)
  - `(auth)/` - Authentication routes (sign-in, sign-up)
- `lib/` - Application code
  - `apps/` - Feature modules (analytics, billing, materials, messages, quiz-attempts, quizes, users)
  - `pb/` - PocketBase client and types
  - `api/` - API client utilities
  - `types/` - TypeScript type definitions
  - `utils/` - Utility functions
  - `assets/` - Static assets
  - `styles/` - Global styles

**Key Dependencies:**

- SvelteKit with adapter-node
- Svelte 5 (modern runes: $state, $derived, $effect)
- Tailwind CSS v4 + daisyUI 5
- PocketBase SDK for auth/data
- Capacitor for mobile apps
- PostHog for analytics
- Stripe.js for payments

**Data Loading:** User layout (`routes/(user)/+layout.ts`) loads all user data (materials, quizes, quiz attempts, subscription) on auth and stores in global Svelte stores.

### Frontend (Web)

**Location:** `apps/web/src/`

**Structure:**

- `pages/` - Astro file-based routing
- `content/` - Content collections (blog, landings, quizes, pages)
- `components/` - Reusable components (uses `@quizbee/astro-sections`)
- `layouts/` - Page layouts
- `ssg/` - Static site generation utilities
- `lib/` - Shared utilities
- `i18n/` - Internationalization

**Key Dependencies:**

- Astro with Node adapter
- Svelte 5 integration for interactive components
- Tailwind CSS v4 + daisyUI 5
- PocketBase SDK
- `@quizbee/astro-sections` for page sections

### Infrastructure

**Services (Docker Compose):**

- **PocketBase** (port 8090) - Database + Auth + File storage
- **Meilisearch** (port 7700) - Search engine
- **Dragonfly** (port 6379) - Redis-compatible cache/queue

**Config:** `infra/compose.local.yml`

## Code Style Guidelines

### Svelte Components

- Use modern Svelte 5 syntax with runes ($state, $derived, $effect)
- Use classical HTML callbacks: `onclick` NOT `on:click`
- Use Tailwind v4 + daisyUI 5 semantic variables
- Use `lucide-svelte` icons instead of inline SVGs
- NEVER use `dark:` variants - theme is handled globally
- Use `@quizbee/ui-svelte-daisy` component library

**Global styles:**

- App: `apps/app/src/app.css`
- Web: `apps/web/src/styles/global.css`

### Astro Pages

- Use `@quizbee/astro-sections` components for pages and landing sections
- Can embed Svelte components for interactivity

## Type Safety

### Python

- Uses Pyright with Python 3.13
- Config: `pyrightconfig.json` (venv in `apps/api/.venv`)
- Strict Pydantic models for validation

### TypeScript

- PocketBase types auto-generated from database
- Generate with: `pnpm build:gen-types` (in web or app directories)
- Located at:
  - App: `src/lib/pb/pocketbase-types.ts`
  - Web: `src/lib/pocketbase-types.ts`

## Package Management & Monorepo Workflow

### Overview

QuizBee uses a **dual-mode workspace** strategy:

- **Development**: Hot-reload workspace packages for fast iteration
- **Production**: Independent app deployments via Coolify using registry packages

### JavaScript/TypeScript (pnpm)

**Configuration:**

- Workspace defined in [pnpm-workspace.yaml](pnpm-workspace.yaml)
- Per-app lock files enabled via [.npmrc](.npmrc) (`shared-workspace-lockfile=false`)
- Workspace protocol: `workspace:*` in dependencies

**Structure:**

```
/
├── pnpm-workspace.yaml        # Workspace config
├── .npmrc                     # Per-app locks config
├── pnpm-lock.yaml             # Root lock (minimal)
├── apps/
│   ├── app/pnpm-lock.yaml    # Per-app lock ✅
│   └── web/pnpm-lock.yaml    # Per-app lock ✅
└── pkgs/
    └── js/pb-types/           # Workspace package
```

**Development Workflow:**

```bash
# Install with workspace symlinks (hot-reload enabled)
pnpm install

# Changes in pkgs/js/* are immediately visible in apps/*
# No rebuild needed - vite watches workspace packages
```

**Production Workflow:**

```bash
# 1. Publish workspace packages to npm (when ready)
cd pkgs/js/pb-types
pnpm publish

# 2. Deploy apps via Coolify
# Each app uses its own pnpm-lock.yaml
# Coolify builds from /apps/app context
# workspace:* dependencies resolved from npm registry
```

**Key Features:**

- ✅ Hot-reload in development
- ✅ Per-app lock files for independent deploys
- ✅ Workspace symlinks (`@quizbee/pb-types -> ../../../../pkgs/js/pb-types`)
- ✅ Coolify deploys from `/apps/app` context with app-specific lock

### Python (uv)

**Configuration:**

- Workspace defined in root [pyproject.toml](pyproject.toml)
- Development uses workspace lock at `/uv.lock`
- Production uses per-app locks (generated via script)

**Structure:**

```
/
├── pyproject.toml             # Workspace root
├── uv.lock                    # Development lock (workspace)
├── apps/
│   └── api/
│       ├── pyproject.toml    # App config with [tool.uv.sources]
│       └── uv.lock           # Production lock (no workspace) ✅
└── pkgs/
    └── python/example-lib/   # Workspace package
```

**Development Workflow:**

```bash
# Sync workspace (hot-reload enabled)
cd /quizbee
uv sync

# Changes in pkgs/python/* are immediately visible in apps/api
# Editable installs via workspace
```

**Production Workflow:**

```bash
# 1. Publish workspace packages to PyPI
cd pkgs/python/example-lib
uv build && uv publish

# 2. Generate production lock (without workspace)
python scripts/python/gen_prod_locks.py

# 3. Commit updated apps/api/uv.lock

# 4. Deploy via Coolify
# Coolify builds from /apps/api context
# Uses apps/api/uv.lock (fetches from PyPI, not workspace)
```

**Key Features:**

- ✅ Hot-reload in development via workspace
- ✅ `[tool.uv.sources]` workspace override for dev
- ✅ Production locks without workspace dependencies
- ✅ Automated script to generate production locks
- ✅ Coolify deploys from `/apps/api` context

### Monorepo Structure

```
/
├── apps/                      # Main applications (deployed independently)
│   ├── api/                  # Python FastAPI backend
│   ├── app/                  # SvelteKit mobile/web app
│   ├── web/                  # Astro marketing site
│   ├── pb/                   # PocketBase
│   ├── meilisearch/          # Search service
│   └── dragonfly/            # Redis cache
├── pkgs/                      # Shared libraries (published to registries)
│   ├── js/
│   │   └── pb-types/         # PocketBase TypeScript types
│   └── python/
│       └── example-lib/      # Example Python library
├── scripts/                   # Build and utility scripts
│   ├── js/
│   └── python/
│       └── gen_prod_locks.py # Generate production lock files
├── pyproject.toml             # Python workspace root
├── pnpm-workspace.yaml        # pnpm workspace config
└── .npmrc                     # pnpm per-app locks config
```

### Publishing Packages

**JavaScript/TypeScript:**

```bash
cd pkgs/js/pb-types
pnpm build                     # Generate types from PocketBase
pnpm publish                   # Publish to npm (@quizbee/pb-types)
```

**Python:**

```bash
cd pkgs/python/example-lib
uv build                       # Build wheel
uv publish                     # Publish to PyPI (quizbee-example-lib)
```

### Lock File Management

**pnpm (automatic):**

- Per-app locks generated automatically via `.npmrc`
- Run `pnpm install` to update locks
- Commit all `apps/*/pnpm-lock.yaml` files

**uv (script-assisted):**

- Development lock: `uv sync` (creates `/uv.lock`)
- Production lock: `python scripts/python/gen_prod_locks.py`
- Commit both `/uv.lock` and `apps/*/uv.lock` files

### Coolify Deployment

Each app deploys independently with its own context:

**API (Python):**

- Context: `/apps/api`
- Dockerfile: `apps/api/Dockerfile`
- Uses: `apps/api/uv.lock` (PyPI dependencies)

**App (SvelteKit):**

- Context: `/apps/app`
- Dockerfile: `apps/app/Dockerfile`
- Uses: `apps/app/pnpm-lock.yaml` (npm dependencies)

**Web (Astro):**

- Context: `/apps/web`
- Dockerfile: `apps/web/Dockerfile`
- Uses: `apps/web/pnpm-lock.yaml` (npm dependencies)

## Environment

- Environment files in `envs/.env`
- App dev server uses: `node --env-file=../../envs/.env`
- API and Docker services load from `envs/.env`

## Testing

- **App:** Vitest (unit) + Playwright (E2E)
- **API:** pytest
- **Integration/E2E:** Located in `tests/` directory
