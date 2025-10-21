/// <reference path="../pb_data/types.d.ts" />

onRecordCreate((e) => {
  // before creation

  if (!e.record.get("kind")) {
    e.record.set("kind", "simple");
  }
  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after creation
}, "materials");

onRecordUpdate((e) => {
  // before update

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after update
}, "materials");

onRecordDelete((e) => {
  // before deletion

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after deletion
}, "materials");
