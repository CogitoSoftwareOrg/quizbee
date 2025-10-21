/// <reference path="../pb_data/types.d.ts" />

onRecordCreate((e) => {
  if (e.record.get("itemsLimit") === 0) {
    e.record.set("itemsLimit", 10);
  }
  if (!e.record.get("status")) {
    e.record.set("status", "draft");
  }
  if (!e.record.get("difficulty")) {
    e.record.set("difficulty", "intermediate");
  }
  if (!e.record.get("visibility")) {
    e.record.set("visibility", "public");
  }

  e.record.set("dynamicConfig", {
    adds: [],
    moreOnTopic: [],
    lessOnTopic: [],
    extraBeginner: [],
    extraExpert: [],
    negativeQuestions: [],
  });

  e.next();

  $app.runInTransaction((txApp) => {});
}, "quizes");

onRecordUpdate((e) => {
  e.next();

  if (e.record.get("status") === "preparing") {
    $app.runInTransaction((txApp) => {
      const col = txApp.findCollectionByNameOrId("quizItems");
      for (let i = 0; i < e.record.get("itemsLimit"); i++) {
        const item = new Record(col);
        item.set("quiz", e.record.id);
        item.set("order", i);
        txApp.save(item);
      }
    });
  }
}, "quizes");

onRecordDelete((e) => {
  e.next();

  $app.runInTransaction((txApp) => {});
}, "quizes");
