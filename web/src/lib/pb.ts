import PocketBase from "pocketbase";

export const pb = new PocketBase(import.meta.env.PB_URL);
