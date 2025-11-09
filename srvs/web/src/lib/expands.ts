import type { QuizItemsResponse } from "./pocketbase-types";

export type QuizExpand = {
  quizItems_via_quiz: QuizItemsResponse[] | undefined;
};
