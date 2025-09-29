/// <reference path="../pb_data/types.d.ts" />

onRecordCreate((e) => {
  // before creation

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
    const col = txApp.findCollectionByNameOrId("subscriptions");
    const record = new Record(col);
    record.set("user", e.record.id);
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