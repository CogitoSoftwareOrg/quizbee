/// <reference path="../pb_data/types.d.ts" />

onRecordCreate((e) => {
  // before creation

  if (!e.record.get("status")) {
    e.record.set("status", "blank");
  }
  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after creation
}, "quizItems");

onRecordUpdate((e) => {
  // before update

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after update
}, "quizItems");

onRecordDelete((e) => {
  // before deletion

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after deletion
}, "quizItems");
