/// <reference path="../pb_data/types.d.ts" />

onRecordUpdate((e) => {
  const feedback = e.record.get("feedback");
  const choices = JSON.parse(e.record.get("choices") ?? "[]");
  const quizId = e.record.get("quiz");

  const quiz = $app.findRecordById("quizes", quizId);
  const limit = quiz.getInt("itemsLimit");

  console.log(feedback, choices.length, limit);
  if (feedback == "null" && limit === choices.length) {
    console.log("feedback set {}");
    e.record.set("feedback", {});
  }

  e.next();
}, "quizAttempts");
