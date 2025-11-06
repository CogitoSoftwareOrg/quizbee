import { test, expect } from "@playwright/test";

test("@smoke главная открывается и виден CTA", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /quizbee/i })).toBeVisible();
  await expect(
    page.getByRole("button", { name: /create quiz/i })
  ).toBeVisible();
});
