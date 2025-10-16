import PocketBase from "pocketbase";

import { urlWithPR } from "./pr-url";

const adminUrl = urlWithPR(import.meta.env.PB_URL);
const publicUrl = urlWithPR(import.meta.env.PUBLIC_PB_URL);

export const pb = new PocketBase(adminUrl);
pb.autoCancellation(false);

export const pbPublic = new PocketBase(publicUrl);
pbPublic.autoCancellation(true);
