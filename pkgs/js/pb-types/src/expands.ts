import type {
  MaterialsResponse,
  QuizesResponse,
  QuizAttemptsResponse,
  QuizItemsResponse,
  SubscriptionsResponse,
} from "./pocketbase-types";

export type QuizExpand = {
  quizItems_via_quiz: QuizItemsResponse[] | undefined;
};

export type QuizAttemptExpand = {
  quiz: QuizesResponse<QuizExpand> | undefined;
};

export type UserExpand = {
  subscriptions_via_user: SubscriptionsResponse[] | undefined;
  materials_via_user: MaterialsResponse[] | undefined;
  quizAttempts_via_user: QuizAttemptsResponse[] | undefined;
  quizes_via_author: QuizesResponse<QuizExpand>[] | undefined;
};
