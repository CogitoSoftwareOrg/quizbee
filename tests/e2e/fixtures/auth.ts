import { test as base, expect } from "@playwright/test";
import { makeApi } from "./api";

type AuthFixtures = {
  token: string;
};

export const test = base.extend<AuthFixtures>({
  token: async ({}, use) => {
    const api = await makeApi(
      process.env.API_URL ?? process.env.PREVIEW_URL ?? ""
    );
    // Пример: завести тестового пользователя/получить токен
    const res = await api.post("/api/auth/login", {
      data: { email: "e2e@quizbee.dev", password: "e2e-pass" },
    });
    const body = await res.json();
    await use(body.token);
    await api.dispose();
  },
});

export const expectEx = expect;
