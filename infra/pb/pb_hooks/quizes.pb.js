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

  const userId = e.record.get("user");
  if (userId) {
    try {
      const userQuizes = $app.findRecordsByFilter(
        "quizes",
        `user = "${userId}"`,
        "-created"
      );

      if (userQuizes.length === 1) {
        return;
      }

      const firstQuizCreated = new Date(userQuizes[userQuizes.length - 1].get("created"));
      const now = new Date();
      const daysSinceFirstQuiz = Math.floor((now - firstQuizCreated) / (1000 * 60 * 60 * 24));

      if (daysSinceFirstQuiz > 0 && daysSinceFirstQuiz <= 7) {
        const uniqueDays = new Set();
        
        userQuizes.forEach((quiz) => {
          const quizDate = new Date(quiz.get("created"));
          const quizDaysSince = Math.floor((quizDate - firstQuizCreated) / (1000 * 60 * 60 * 24));
          if (quizDaysSince <= 7) {
            uniqueDays.add(quizDaysSince);
          }
        });

        if (uniqueDays.size >= 2) {
          const user = $app.findRecordById("users", userId);
          const email = user.get("email");
          
          $http.send({
            url: "https://eu.i.posthog.com/capture/",
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              api_key: process.env.PUBLIC_POSTHOG_KEY || "",
              event: "user_active_two_days_after_first_quiz",
              properties: {
                distinct_id: userId,
                email: email,
                activeDays: uniqueDays.size,
                daysSinceFirstQuiz: daysSinceFirstQuiz
              }
            }),
            timeout: 10
          });
        }
      }
    } catch (err) {
      console.error("Failed to track first quiz activity:", err);
    }
  }
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
