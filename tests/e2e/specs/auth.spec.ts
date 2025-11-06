import { test, expect } from "@playwright/test";
import { TEST_USER } from "../fixtures/pb";

test("логин через UI и выход", async ({ page }) => {
  await page.goto("/sign-in");
  await page.getByLabel(/email/i).fill(TEST_USER.email);
  await page.getByLabel(/password/i).fill(TEST_USER.password);
  await page.locator('button[type="submit"]', { hasText: /sign in/i }).click();

  await expect(page).toHaveURL(/\/home/);

  // Then check there's a profile button/link
  const profileButton = page.getByRole("link", {
    name: "avatar E2E Test User",
  });
  await expect(profileButton).toBeVisible();
  await profileButton.click();

  // Then click Logout button
  await page.locator("button", { hasText: "Logout" }).click();
  await expect(page).toHaveURL(/\/sign-in/);
});
