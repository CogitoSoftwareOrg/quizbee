import { test as base, expect } from "@playwright/test";
import { makeApi } from "./api";
import { TEST_USER } from "./pb";

type AuthFixtures = {
  token: string;
};

export const test = base.extend<AuthFixtures>({
  token: async ({}, use) => {
    const api = await makeApi(
      process.env.API_URL ?? process.env.PREVIEW_URL ?? ""
    );
    // Login with test user
    const res = await api.post("/api/auth/login", {
      data: { email: TEST_USER.email, password: TEST_USER.password },
    });
    const body = await res.json();
    await use(body.token);
    await api.dispose();
  },
});

export const expectEx = expect;
