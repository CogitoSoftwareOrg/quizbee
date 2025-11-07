import PocketBase from "pocketbase";

/**
 * Create test materials for the test user
 */
export async function createTestMaterial(pb: PocketBase, title: string) {
  const user = pb.authStore.record;
  if (!user) throw new Error("User not authenticated");

  return await pb.collection("materials").create({
    title,
    contents: { type: "text", data: `Test content for ${title}` },
    user: user.id,
  });
}

/**
 * Create test quiz for the test user
 */
export async function createTestQuiz(pb: PocketBase, title: string) {
  const user = pb.authStore.record;
  if (!user) throw new Error("User not authenticated");

  return await pb.collection("quizes").create({
    title,
    user: user.id,
    status: "draft",
    visibility: "private",
  });
}

/**
 * Clean up test data created by the user
 */
export async function cleanupTestData(pb: PocketBase) {
  const user = pb.authStore.record;
  if (!user) return;

  try {
    // Delete all quizes
    const quizes = await pb.collection("quizes").getFullList({
      filter: `user = "${user.id}"`,
    });
    for (const quiz of quizes) {
      await pb.collection("quizes").delete(quiz.id);
    }

    // Delete all materials
    const materials = await pb.collection("materials").getFullList({
      filter: `user = "${user.id}"`,
    });
    for (const material of materials) {
      await pb.collection("materials").delete(material.id);
    }

    console.log("✓ Test data cleaned up");
  } catch (error) {
    console.error("Failed to cleanup test data:", error);
  }
}
