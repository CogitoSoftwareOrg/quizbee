import PocketBase from "pocketbase";
import { config } from "dotenv";
import { resolve } from "path";

// Load environment variables from envs/.env
config({ path: resolve(process.cwd(), "../../envs/.env") });

const PB_URL = process.env.PUBLIC_PB_URL || "http://localhost:8090";
const PB_EMAIL = process.env.PB_EMAIL || "admin@admin.com";
const PB_PASSWORD = process.env.PB_PASSWORD || "admin";

async function updateQuizesVisibility() {
  const pb = new PocketBase(PB_URL);

  try {
    console.log("Authenticating as admin...");
    await pb.collection("_superusers").authWithPassword(PB_EMAIL, PB_PASSWORD);
    console.log("✓ Authenticated successfully");

    console.log("\nFetching all quizes...");
    const quizes = await pb.collection("quizes").getFullList({
      fields: "id,visibility",
    });
    console.log(`✓ Found ${quizes.length} quizes`);

    console.log("\nUpdating visibility to 'search'...");
    let updated = 0;
    let skipped = 0;

    for (const quiz of quizes) {
      if (quiz.visibility === "search") {
        skipped++;
        continue;
      }

      try {
        await pb.collection("quizes").update(quiz.id, {
          visibility: "search",
        });
        updated++;
        process.stdout.write(`\r✓ Updated ${updated}/${quizes.length}`);
      } catch (error) {
        console.error(`\n✗ Failed to update quiz ${quiz.id}:`, error.message);
      }
    }

    console.log(`\n\n✓ Completed!`);
    console.log(`  - Updated: ${updated}`);
    console.log(`  - Skipped (already 'search'): ${skipped}`);
    console.log(`  - Total: ${quizes.length}`);
  } catch (error) {
    console.error("✗ Error:", error.message);
    process.exit(1);
  }
}

updateQuizesVisibility();
