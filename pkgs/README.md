# QuizBee Shared Packages

This directory contains shared libraries used across QuizBee applications.

## Structure

```
pkgs/
├── js/                 # JavaScript/TypeScript packages
│   └── pb-types/      # PocketBase TypeScript types
└── python/            # Python packages
    └── example-lib/   # Example shared library
```

## Development Workflow

### Hot-Reload in Development

When developing packages locally, changes are automatically reflected in consuming apps:

**JavaScript:**
```bash
# From monorepo root
pnpm install           # Creates workspace symlinks

# Edit pkgs/js/pb-types/src/index.ts
# Changes immediately visible in apps/app and apps/web
# Vite watches workspace packages automatically
```

**Python:**
```bash
# From monorepo root
uv sync                # Creates editable installs

# Edit pkgs/python/example-lib/src/quizbee_example_lib/__init__.py
# Changes immediately visible in apps/api
# FastAPI auto-reloads on file changes
```

## Publishing Packages

Before deploying apps to production, publish updated packages to registries.

### JavaScript Packages

```bash
cd pkgs/js/pb-types

# Update version in package.json
# Edit version: "0.1.0" -> "0.2.0"

# Build (if needed)
pnpm build

# Publish to npm
pnpm publish

# Update consuming apps
cd ../../apps/app
# pnpm will auto-update to new version on next install
```

### Python Packages

```bash
cd pkgs/python/example-lib

# Update version in pyproject.toml
# Edit version: "0.1.0" -> "0.2.0"

# Build wheel
uv build

# Publish to PyPI
uv publish

# Generate production locks for consuming apps
cd ../../../
python scripts/python/gen_prod_locks.py
```

## Adding New Packages

### JavaScript Package

```bash
mkdir -p pkgs/js/my-package
cd pkgs/js/my-package

# Create package.json
cat > package.json << 'EOF'
{
  "name": "@quizbee/my-package",
  "version": "0.1.0",
  "type": "module",
  "main": "src/index.ts",
  "types": "src/index.ts",
  "publishConfig": {
    "access": "public"
  }
}
EOF

# Create source
mkdir -p src
echo "export const hello = 'world'" > src/index.ts

# Use in apps
cd ../../apps/app
# Add to package.json dependencies:
# "@quizbee/my-package": "workspace:*"
pnpm install
```

### Python Package

```bash
mkdir -p pkgs/python/my-package/src/quizbee_my_package
cd pkgs/python/my-package

# Create pyproject.toml
cat > pyproject.toml << 'EOF'
[project]
name = "quizbee-my-package"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/quizbee_my_package"]
EOF

# Create source
echo '__version__ = "0.1.0"' > src/quizbee_my_package/__init__.py
touch src/quizbee_my_package/py.typed

# Use in apps
cd ../../apps/api
# Add to pyproject.toml dependencies:
# "quizbee-my-package>=0.1.0"
# Add to [tool.uv.sources]:
# quizbee-my-package = { workspace = true }

# Sync workspace
cd ../..
uv sync
```

## Package Naming Conventions

- **JavaScript/TypeScript**: `@quizbee/package-name` (scoped)
- **Python**: `quizbee-package-name` (hyphenated)

## Best Practices

1. **Version Management**: Use semantic versioning (semver)
2. **Breaking Changes**: Bump major version for breaking API changes
3. **Testing**: Add tests to packages before publishing
4. **Documentation**: Include README.md in each package
5. **Type Safety**:
   - JS: Export TypeScript types
   - Python: Include `py.typed` marker file
6. **Dependencies**: Keep package dependencies minimal
7. **Publishing**: Always test locally with workspace before publishing

## Troubleshooting

### JavaScript: Package not updating in apps

```bash
# Clear node_modules and reinstall
rm -rf node_modules apps/*/node_modules
pnpm install
```

### Python: Package not updating in apps

```bash
# Re-sync workspace
uv sync --reinstall
```

### Production lock out of sync

```bash
# Regenerate production locks
python scripts/python/gen_prod_locks.py
```
