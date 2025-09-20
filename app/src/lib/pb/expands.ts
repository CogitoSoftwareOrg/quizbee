import type {
	MaterialsResponse,
	QuizesResponse,
	QuizAttemptsResponse,
	QuizItemsResponse,
	SubscriptionsResponse
} from './pocketbase-types';

export type UserExpand = {
	subscription: SubscriptionsResponse | undefined;
	materials_via_user: MaterialsResponse[] | undefined;
	quizAttempts_via_user: QuizAttemptsResponse[] | undefined;
	quizes_via_user: QuizesResponse[] | undefined;
};

export type QuizExpand = {
	quizItems_via_quiz: QuizItemsResponse[] | undefined;
};
