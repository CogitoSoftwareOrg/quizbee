export function urlWithPR(raw?: string | URL) {
  if (!raw) throw new Error("urlWithPR: empty url");
  const u = new URL(typeof raw === "string" ? raw : raw.toString());

  const env =
    (import.meta as any).env?.PUBLIC_ENV ?? process.env.RUNTIME_PUBLIC_ENV;
  const coolify =
    (import.meta as any).env?.COOLIFY_URL ?? process.env.RUNTIME_COOLIFY_URL;

  if (env === "preview" && coolify) {
    // валидируем только если реально есть coolify
    const cu = new URL(coolify);
    const pr = cu.hostname.split("-")[0];
    u.hostname = `${pr}-${u.hostname}`;
  }
  return u.toString();
}
