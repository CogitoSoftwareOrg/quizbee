/// <reference path="../pb_data/types.d.ts" />

onRecordCreate((e) => {
  e.record.set("status", "active");
  e.record.set("tariff", "free");
  e.record.set("stripeInterval", "month");
  e.record.set("currentPeriodStart", new Date().toISOString());
  e.record.set(
    "currentPeriodEnd",
    new Date(
      Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth() + 100, 1)
    ).toISOString()
  );
  // MONTHLY LIMITS FOR FREE USERS
  e.record.set("quizItemsLimit", 50);
  e.record.set("messagesLimit", 50);
  e.record.set("storageLimit", 2 * 1024 * 1024 * 1024);

  e.next();

  $app.runInTransaction((txApp) => {});
}, "subscriptions");

onRecordUpdate((e) => {
  const oldUsage = e.record.originalCopy().get("quizItemsUsage") || 0;
  const newUsage = e.record.get("quizItemsUsage") || 0;

  if (oldUsage < 40 && newUsage >= 40) {
    const userId = e.record.get("user");
    
    try {
      const user = $app.findRecordById("users", userId);
      const email = user.get("email");
      
      $http.send({
        url: "https://eu.i.posthog.com/capture/",
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          api_key: process.env.PUBLIC_POSTHOG_KEY || "",
          event: "quiz_items_usage_threshold_reached",
          properties: {
            distinct_id: userId,
            email: email,
            usage: newUsage,
            threshold: 40
          }
        }),
        timeout: 10
      });
    } catch (err) {
      console.error("Failed to send posthog event:", err);
    }
  }

  e.next();
}, "subscriptions");

cronAdd("subscriptions_usage_reset_daily", "0 0 * * *", () => {
  const now = new Date();
  const subs = $app.findRecordsByFilter(
    "subscriptions",
    "status = 'active' || status = 'trialing' || status = 'past_due'"
  );
});

cronAdd("subscriptions_usage_reset_monthly", "0 0 1 * *", () => {
  const now = new Date();
  const subs = $app.findRecordsByFilter(
    "subscriptions",
    "status = 'active' || status = 'trialing' || status = 'past_due'"
  );

  subs.forEach((s) => {
    s.set("lastUsageResetAt", now.toISOString());
    s.set("quizItemsUsage", 0);
    $app.save(s);
  });
});
