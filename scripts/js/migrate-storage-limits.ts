import PocketBase from "pocketbase";
import { config } from "dotenv";
import { resolve } from "path";

// Load environment variables from envs/.env
config({ path: resolve(process.cwd(), "../../envs/.env.production") });

const PB_URL = process.env.PUBLIC_PB_URL || "http://localhost:8090";
const PB_EMAIL = process.env.PB_EMAIL || "admin@admin.com";
const PB_PASSWORD = process.env.PB_PASSWORD || "admin";

// Storage limits based on tariff (in bytes)
const STORAGE_LIMITS: Record<string, number> = {
  free: 2 * 1024 * 1024 * 1024, // 2GB
  plus: 10 * 1024 * 1024 * 1024, // 10GB
  pro: 100 * 1024 * 1024 * 1024, // 100GB
};

interface Subscription {
  id: string;
  tariff: string;
  storageLimit?: number;
}

async function migrateStorageLimits() {
  const pb = new PocketBase(PB_URL);

  try {
    console.log("Authenticating as admin...");
    await pb.collection("_superusers").authWithPassword(PB_EMAIL, PB_PASSWORD);
    console.log("✓ Authenticated successfully");

    console.log("\nFetching all subscriptions...");
    const subscriptions = await pb
      .collection("subscriptions")
      .getFullList<Subscription>({
        fields: "id,tariff,storageLimit",
      });
    console.log(`✓ Found ${subscriptions.length} subscriptions`);

    console.log("\nUpdating storage limits based on tariff...");
    let updated = 0;
    let skipped = 0;
    let errors = 0;

    for (const subscription of subscriptions) {
      const tariff = subscription.tariff?.toLowerCase();
      const expectedLimit = STORAGE_LIMITS[tariff];

      if (!expectedLimit) {
        console.warn(
          `\n⚠ Unknown tariff '${subscription.tariff}' for subscription ${subscription.id}`
        );
        errors++;
        continue;
      }

      if (subscription.storageLimit === expectedLimit) {
        skipped++;
        continue;
      }

      try {
        await pb.collection("subscriptions").update(subscription.id, {
          storageLimit: expectedLimit,
        });
        updated++;
        process.stdout.write(
          `\r✓ Updated ${updated}/${subscriptions.length} (${subscription.tariff}: ${expectedLimit / (1024 * 1024 * 1024)}GB)`
        );
      } catch (error: any) {
        console.error(
          `\n✗ Failed to update subscription ${subscription.id}:`,
          error.message
        );
        errors++;
      }
    }

    console.log("\n\n✓ Migration completed!");
    console.log(`  - Updated: ${updated}`);
    console.log(`  - Skipped (already correct): ${skipped}`);
    console.log(`  - Errors: ${errors}`);
    console.log(`  - Total: ${subscriptions.length}`);

    console.log("\nStorage limit distribution:");
    for (const [tariff, limit] of Object.entries(STORAGE_LIMITS)) {
      const count = subscriptions.filter(
        (s) => s.tariff?.toLowerCase() === tariff
      ).length;
      if (count > 0) {
        console.log(
          `  - ${tariff}: ${count} subscriptions → ${limit / (1024 * 1024 * 1024)}GB`
        );
      }
    }
  } catch (error: any) {
    console.error("✗ Error:", error.message);
    process.exit(1);
  }
}

migrateStorageLimits();
