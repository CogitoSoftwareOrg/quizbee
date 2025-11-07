import { test as base } from "@playwright/test";
import { createPBClient, authenticateTestUser } from "./pb";
import PocketBase from "pocketbase";

type TestFixtures = {
  pb: PocketBase;
  authenticatedPb: PocketBase;
};

export const test = base.extend<TestFixtures>({
  // Basic PB client without auth
  pb: async ({}, use) => {
    const pbUrl = process.env.PUBLIC_PB_URL || "http://localhost:8090";
    const pb = await createPBClient(pbUrl);
    await use(pb);
  },

  // Authenticated PB client with test user
  authenticatedPb: async ({ pb }, use) => {
    await authenticateTestUser(pb);
    await use(pb);
  },
});

export { expect } from "@playwright/test";
