/// <reference path="../pb_data/types.d.ts" />

onRecordCreate((e) => {
  // before creation
  if (e.record.get("itemsLimit") === 0) {
    e.record.set("itemsLimit", 10);
  }
  if (!e.record.get("status")) {
    e.record.set("status", "draft");
  }
  if (!e.record.get("difficulty")) {
    e.record.set("difficulty", "intermediate");
  }

  e.record.set("dynamicConfig", {
    adds: [],
    moreOnTopic: [],
    lessOnTopic: [],
    extraBeginner: [],
    extraExpert: [],
  });

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
    const col = txApp.findCollectionByNameOrId("quizItems");
    for (let i = 0; i < e.record.get("itemsLimit"); i++) {
      const item = new Record(col);
      item.set("quiz", e.record.id);
      item.set("order", i);
      txApp.save(item);
    }
  });

  // after creation
}, "quizes");

onRecordUpdate((e) => {
  // before update

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after update
}, "quizes");

onRecordDelete((e) => {
  // before deletion

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after deletion
}, "quizes");
