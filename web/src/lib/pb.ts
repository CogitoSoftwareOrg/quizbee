import PocketBase from "pocketbase";

import { urlWithPR } from "./pr-url";

const url = urlWithPR(import.meta.env.PB_URL ?? import.meta.env.PUBLIC_PB_URL);

export const pb = new PocketBase(url);
if (typeof window === "undefined") pb.autoCancellation(false);
