/// <reference path="../pb_data/types.d.ts" />

onRecordUpdate((e) => {
  const choices = JSON.parse(e.record.get("choices") ?? "[]");
  const quizId = e.record.get("quiz");

  const quiz = $app.findRecordById("quizes", quizId);

  if (!e.record.get("feedback") && quiz.get("itemsLimit") === choices.length) {
    e.record.set("feedback", {});
  }

  e.next();
}, "quizAttempts");
