import { test, expect } from "@playwright/test";

test("логин через UI и выход", async ({ page }) => {
  await page.goto("/sign-in");
  await page.getByLabel(/email/i).fill("e2e@quizbee.dev");
  await page.getByLabel(/password/i).fill("e2e-pass");
  await page.getByRole("button", { name: /sign in/i }).click();

  await expect(page.getByText(/welcome/i)).toBeVisible();
  await page.getByRole("button", { name: /logout/i }).click();
  await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
});
