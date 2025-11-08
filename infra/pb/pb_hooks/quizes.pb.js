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
}, "quizes");

onRecordUpdate((e) => {
  e.next();

  const status = e.record.get("status");
  const quizId = e.record.id;

  if (status === "preparing") {
    const existingItems = $app.findRecordsByFilter(
      "quizItems",
      `quiz = "${quizId}"`
    );

    if (existingItems.length === 0) {
      $app.runInTransaction((txApp) => {
        const quizItemsCol = txApp.findCollectionByNameOrId("quizItems");
        const itemsLimit = e.record.get("itemsLimit") || 10;
        for (let i = 0; i < itemsLimit; i++) {
          const item = new Record(quizItemsCol);
          item.set("quiz", quizId);
          item.set("order", i);
          txApp.save(item);
        }
      });
    }
  }
}, "quizes");

onRecordDelete((e) => {
  e.next();

  $app.runInTransaction((txApp) => {});
}, "quizes");
