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
