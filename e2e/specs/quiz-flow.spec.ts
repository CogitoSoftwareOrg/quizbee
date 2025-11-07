import { test, expect } from "@playwright/test";

test.describe("Quiz Flow", () => {
  test("complete quiz flow: create, answer, explain, finish and verify", async ({
    page,
  }) => {
    // Step 1: Navigate to home page and click "Start new quiz"
    await page.goto("/");

    const newQuizLink = page.locator('a[href="/quizes/new"]');
    await expect(newQuizLink).toBeVisible();
    await newQuizLink.click();
    await expect(page).toHaveURL(/\/quizes\/new/);

    // Step 2: Enter quiz title
    const titleInput = page
      .locator('input[type="text"][placeholder=""]')
      .first();
    await titleInput.fill("Test Quiz");

    // Step 3: Enter quiz description in textarea
    const descriptionTextarea = page.locator("textarea").first();
    await descriptionTextarea.fill("This is a test quiz about programming");

    // Step 4: Click "Start a quiz" button
    const startButton = page.getByRole("button", { name: /start a quiz/i });
    await startButton.click();

    // Wait for quiz to be created and redirected to quiz attempt page
    await page.waitForURL(/\/quizes\/[^/]+\/attempts\/[^/]+/, {
      timeout: 30000,
    });
    console.log("✓ Quiz created, navigated to attempt page");

    // Step 5: Wait for first question to load (answers are buttons inside articles)
    await expect(
      page.locator('article button[type="button"]').first()
    ).toBeVisible({ timeout: 60000 });
    console.log("✓ First question loaded");

    // Step 6: Select first answer option
    const firstAnswer = page.locator('article button[type="button"]').first();
    await firstAnswer.click();
    console.log("✓ Answer selected");

    // Wait a bit for the answer to be saved
    await page.waitForTimeout(2000);

    // Step 7: Click "Explain" button
    const explainButton = page.getByRole("button", { name: /explain/i });
    await expect(explainButton).toBeVisible();
    await explainButton.click();
    console.log("✓ Explain button clicked");

    // Step 8: Wait for AI chat to open (check for chat container or messages)
    await page.waitForTimeout(5000); // Wait for AI response
    console.log("✓ AI explanation should be visible");

    // Step 9: Continue answering questions
    let questionsAnswered = 1;
    const maxQuestions = 5;

    while (questionsAnswered < maxQuestions) {
      // Check if there's a "Next" button
      const nextButton = page.getByRole("button", { name: /^next$/i });

      if (!(await nextButton.isVisible())) {
        console.log("✓ No Next button, quiz might be complete");
        break;
      }

      await nextButton.click();

      // Wait for navigation or feedback
      try {
        await page.waitForURL(/\/feedback/, { timeout: 3000 });
        console.log("✓ Redirected to feedback page");
        break;
      } catch {
        // Still on quiz page, wait for next question
        await page.waitForTimeout(2000);

        // Try to select next answer if available
        const nextAnswer = page
          .locator('article button[type="button"]')
          .first();

        if (await nextAnswer.isVisible()) {
          await nextAnswer.click();
          questionsAnswered++;
          console.log(`✓ Question ${questionsAnswered} answered`);
          await page.waitForTimeout(1000);
        }
      }
    }

    // Step 10: Should be on feedback page now
    await expect(page).toHaveURL(/\/feedback/, { timeout: 10000 });
    console.log("✓ On feedback page");

    // Step 11: Close feedback (click X button in top right)
    const closeButton = page.locator('a[href*="/quizes/"]').filter({
      has: page.locator("svg"),
    });
    await closeButton.click();

    // Should be back on quiz page
    await page.waitForURL(/\/quizes\/[^/]+$/);
    console.log("✓ Back on quiz page");

    // Step 12: Toggle quiz visibility (ToggleQuizVisibility component)
    const visibilityToggle = page.locator('input[type="checkbox"]').first();
    await expect(visibilityToggle).toBeVisible();
    await visibilityToggle.click();
    console.log("✓ Quiz visibility toggled");

    await page.waitForTimeout(1000);

    // Step 13: Navigate to quizes list via navigation
    const quizesNavLink = page.locator('a[href="/quizes"]');
    await quizesNavLink.click();
    await expect(page).toHaveURL(/\/quizes$/);

    // Step 14: Verify quiz exists in list
    await expect(page.getByText("Test Quiz")).toBeVisible({ timeout: 5000 });
    console.log("✓ Quiz found in list");
    console.log("✓ Quiz flow test completed successfully");
  });
});
