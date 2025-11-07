import { chromium } from "@playwright/test";
import {
  createPBClient,
  ensureTestUser,
  authenticateTestUser,
  TEST_USER,
} from "./fixtures/pb";

export default async () => {
  const pbUrl = process.env.PUBLIC_PB_URL || "http://localhost:8090";
  const appUrl = process.env.PREVIEW_URL || "http://localhost:5173";

  // Step 1: Create test user in PocketBase
  console.log("Setting up test user in PocketBase...");
  const pb = await createPBClient(pbUrl);
  await ensureTestUser(pb);

  // Step 2: Login via UI to create browser session
  console.log("Creating authenticated browser session...");
  const browser = await chromium.launch();
  const context = await browser.newContext({ baseURL: appUrl });
  const page = await context.newPage();

  await page.goto("/sign-in");
  await page.getByLabel(/email/i).fill(TEST_USER.email);
  await page.getByLabel(/password/i).fill(TEST_USER.password);
  await page.locator('button[type="submit"]', { hasText: /sign in/i }).click();

  // Wait for redirect after successful login
  await page.waitForURL(/\/(quizes|dashboard|home)/, { timeout: 10000 });

  await page.context().storageState({ path: "storageState.json" });
  await browser.close();

  console.log("✓ Global setup complete");
};
