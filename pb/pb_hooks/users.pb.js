/// <reference path="../pb_data/types.d.ts" />

onRecordCreate((e) => {
  // before creation

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
    const col = txApp.findCollectionByNameOrId("subscriptions");
    const record = new Record(col);
    record.set("user", e.record.id);
    record.set("status", "active");
    record.set("tariff", "free");

    // DAILY USAGE
    record.set("quizItemsLimit", 20);
    record.set("messagesLimit", 10);
    txApp.save(record);
  });

  // after creation
}, "users");

onRecordUpdate((e) => {
  // before update

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after update
}, "users");

onRecordDelete((e) => {
  // before deletion

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after deletion
}, "users");

cronAdd("free_users_daily_reset", "0 0 * * *", () => {
  const subs = $app.findRecordsByFilter("subscriptions", "tariff = 'free'");
  subs.forEach((s) => {
    s.set("quizItemsUsage", 0);
    s.set("messagesUsage", 0);
    $app.save(s);
  });
});
