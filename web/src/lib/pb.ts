import PocketBase from "pocketbase";

export function extractPrIdFromCoolifyUrl(coolify: string) {
  const url = new URL(coolify);
  const prId = url.hostname.split(".")[0];
  return prId;
}

let url = import.meta.env.PB_URL;
const coolify = import.meta.env.COOLIFY_URL;

if (import.meta.env.PUBLIC_ENV === "preview" && coolify) {
  const prId = extractPrIdFromCoolifyUrl(coolify);
  url = url.replace("https://", `https://${prId}-`);
}

export const pb = new PocketBase(url);
if (typeof window === "undefined") pb.autoCancellation(false);
