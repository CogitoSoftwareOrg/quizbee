import { createPBClient, cleanupTestUser } from "./fixtures/pb";

export default async () => {
  const pbUrl = process.env.PUBLIC_PB_URL || "http://localhost:8090";

  console.log("Cleaning up test data...");
  const pb = await createPBClient(pbUrl);
  await cleanupTestUser(pb);

  console.log("✓ Global teardown complete");
};
