import PocketBase from "pocketbase";

import type { TypedPocketBase } from "@quizbee/pb-types";

import { urlWithPR } from "./pr-url";

const adminUrl = urlWithPR(
  import.meta.env.PB_URL ?? process.env.RUNTIME_PB_URL
);
const publicUrl = urlWithPR(
  import.meta.env.PUBLIC_PB_URL ?? process.env.RUNTIME_PUBLIC_PB_URL
);

export const pb = new PocketBase(adminUrl) as TypedPocketBase;
pb.autoCancellation(false);

export const pbPub = new PocketBase(publicUrl) as TypedPocketBase;
pbPub.autoCancellation(true);
