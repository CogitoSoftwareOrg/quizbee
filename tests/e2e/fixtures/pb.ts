import PocketBase from "pocketbase";

export const TEST_USER = {
  email: "e2e@quizbee.dev",
  password: "e2e-pass-secure-123",
  name: "E2E Test User",
};

export async function createPBClient(url: string): Promise<PocketBase> {
  return new PocketBase(url);
}

export async function createAdminPBClient(url: string): Promise<PocketBase> {
  const pb = new PocketBase(url);
  await pb
    .collection("_superusers")
    .authWithPassword(process.env.PB_EMAIL!, process.env.PB_PASSWORD!);
  return pb;
}

export async function ensureTestUser(pb: PocketBase) {
  const adminPB = await createAdminPBClient(process.env.PUBLIC_PB_URL!);

  try {
    // Try to find existing user
    const users = await pb.collection("users").getFullList({
      filter: `email = "${TEST_USER.email}"`,
    });

    if (users.length > 0) {
      console.log("✓ Test user already exists");
      return users[0];
    }

    // Create new user
    const user = await pb.collection("users").create({
      email: TEST_USER.email,
      password: TEST_USER.password,
      passwordConfirm: TEST_USER.password,
      name: TEST_USER.name,
      emailVisibility: true,
    });

    // Mark as verified by updating the user
    await adminPB.collection("users").update(user.id, {
      verified: true,
    });

    console.log("✓ Test user created:", TEST_USER.email);
    return user;
  } catch (error) {
    console.error("Failed to create test user:", error);
    throw error;
  }
}

export async function cleanupTestUser(pb: PocketBase) {
  const adminPB = await createAdminPBClient(process.env.PUBLIC_PB_URL!);
  try {
    const users = await adminPB.collection("users").getFullList({
      filter: `email = "${TEST_USER.email}"`,
    });

    for (const user of users) {
      await adminPB.collection("users").delete(user.id);
    }

    console.log("✓ Test user cleaned up");
  } catch (error) {
    console.error("Failed to cleanup test user:", error);
    // Don't throw - cleanup should be graceful
  }
}

export async function authenticateTestUser(pb: PocketBase) {
  await pb
    .collection("users")
    .authWithPassword(TEST_USER.email, TEST_USER.password);
  return pb.authStore.token;
}
