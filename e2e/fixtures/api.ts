import { APIRequestContext, request, expect } from "@playwright/test";

export async function makeApi(
  baseURL: string,
  token?: string
): Promise<APIRequestContext> {
  return await request.newContext({
    baseURL,
    extraHTTPHeaders: token ? { Authorization: `Bearer ${token}` } : {},
  });
}

export async function healthcheck(api: APIRequestContext) {
  const res = await api.get("/health");
  expect(res.ok()).toBeTruthy();
}
