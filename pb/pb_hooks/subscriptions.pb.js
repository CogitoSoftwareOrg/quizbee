/// <reference path="../pb_data/types.d.ts" />

onRecordCreate((e) => {
  e.record.set("status", "active");
  e.record.set("tariff", "free");
  // DAILY USAGE
  e.record.set("quizItemsLimit", 20);
  e.record.set("messagesLimit", 10);
  e.record.set("quizesLimit", 3);

  e.next();

  $app.runInTransaction((txApp) => {});
}, "subscriptions");

cronAdd("free_users_daily_reset", "0 0 * * *", () => {
  const subs = $app.findRecordsByFilter("subscriptions", "tariff = 'free'");
  subs.forEach((s) => {
    s.set("quizItemsUsage", 0);
    s.set("messagesUsage", 0);
    s.set("quizesUsage", 0);
    $app.save(s);
  });
});
