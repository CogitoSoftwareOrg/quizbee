# Storage Limits Migration Script

This script migrates all subscriptions in the database to set `storageLimit` based on their tariff.

## Storage Limits by Tariff

- **Free**: 2GB (2,147,483,648 bytes)
- **Plus**: 10GB (10,737,418,240 bytes)
- **Pro**: 100GB (107,374,182,400 bytes)

## Prerequisites

1. Make sure you have access to PocketBase credentials
2. Ensure the environment variables are set in `../../envs/.env`:
   - `PUBLIC_PB_URL` (or defaults to `http://localhost:8090`)
   - `PB_EMAIL` (admin email)
   - `PB_PASSWORD` (admin password)

## Installation

```bash
cd scripts/js
pnpm install
```

## Usage

```bash
cd scripts/js
pnpm migrate-storage-limits
```

## What it does

1. Connects to PocketBase as admin
2. Fetches all subscriptions from the database
3. For each subscription:
   - Determines the correct storage limit based on the tariff
   - Updates the `storageLimit` field if it doesn't match the expected value
   - Skips subscriptions that already have the correct limit
4. Displays a summary of:
   - Number of subscriptions updated
   - Number of subscriptions skipped (already correct)
   - Number of errors (if any)
   - Distribution of tariffs and their limits

## Example Output

```
Authenticating as admin...
✓ Authenticated successfully

Fetching all subscriptions...
✓ Found 150 subscriptions

Updating storage limits based on tariff...
✓ Updated 147/150 (pro: 100GB)

✓ Migration completed!
  - Updated: 147
  - Skipped (already correct): 3
  - Errors: 0
  - Total: 150

Storage limit distribution:
  - free: 50 subscriptions → 2GB
  - plus: 75 subscriptions → 10GB
  - pro: 25 subscriptions → 100GB
```

## Safety

- The script only updates the `storageLimit` field
- It skips subscriptions that already have the correct value
- It logs any errors but continues processing other subscriptions
- You can safely run this script multiple times (it's idempotent)
