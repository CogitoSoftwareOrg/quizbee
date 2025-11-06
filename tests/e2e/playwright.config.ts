import { defineConfig, devices } from "@playwright/test";
import * as dotenv from "dotenv";

dotenv.config({ path: "../../envs/.env" });

const baseURL =
  process.env.PREVIEW_URL?.replace(/\/$/, "") ||
  process.env.BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:5173"; // поставьте свой дефолт

export default defineConfig({
  testDir: "./specs",
  timeout: 45_000,
  expect: { timeout: 5_000 },
  retries: 1,
  fullyParallel: true,
  reporter: [["html", { open: "never" }], ["list"]],
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    actionTimeout: 10_000,
    navigationTimeout: 20_000,
    storageState: "storageState.json",
  },
  globalSetup: "./globalSetup.ts",
  globalTeardown: "./globalTeardown.ts",
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    // Можно добавить мобильные профили, если нужно:
    // { name: 'mobile', use: { ...devices['Pixel 7'] } },
  ],
  // Если хотите поднимать локальную среду автоматически (см. раздел ниже):
  // webServer: {
  //   command: 'docker compose -f docker-compose.e2e.yml up --build',
  //   port: 5173,
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120_000
  // }
});
