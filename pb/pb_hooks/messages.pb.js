/// <reference path="../pb_data/types.d.ts" />

onRecordCreate((e) => {
  // before creation

  if (!e.record.get("status")) {
    e.record.set("status", "final");
  }
  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after creation
}, "messages");

onRecordUpdate((e) => {
  // before update

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after update
}, "messages");

onRecordDelete((e) => {
  // before deletion

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after deletion
}, "messages");
