function extractPrIdFromCoolifyUrl(coolify: string) {
  const url = new URL(coolify);
  const prId = url.hostname.split(".")[0];
  return prId;
}

const coolify = import.meta.env.COOLIFY_URL;

export function urlWithPR(url: string | URL) {
  if (import.meta.env.PUBLIC_ENV === "preview" && coolify) {
    const prId = extractPrIdFromCoolifyUrl(coolify);
    return new URL(url).toString().replace("https://", `https://${prId}-`);
  }
  return new URL(url).toString();
}
