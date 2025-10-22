import type { QuizAttemptsResponse, QuizesResponse } from '@quizbee/pb-types';

/**
 * Ensures value is an array of choices
 */
export function ensureChoicesArray(value: unknown): unknown[] {
	if (!value) return [];
	if (Array.isArray(value)) return value;
	if (typeof value === 'string') {
		try {
			const parsed = JSON.parse(value);
			return Array.isArray(parsed) ? parsed : [];
		} catch (error) {
			console.error(error);
			return [];
		}
	}
	return [];
}

/**
 * Filters valid quiz attempts (with feedback and final quiz status)
 */
export function getValidAttempts(
	quizAttempts: QuizAttemptsResponse[] | null,
	quizes: QuizesResponse[] | null
): QuizAttemptsResponse[] {
	if (!quizAttempts?.length || !quizes?.length) return [];
	return quizAttempts.filter((attempt) => {
		const choices = ensureChoicesArray(attempt.choices);
		const quiz = quizes.find((q) => q.id === attempt.quiz);

		if (choices.length !== quiz?.itemsLimit) return false;
		return quiz?.status === 'final';
	});
}

/**
 * Gets the start of the current week (Monday at 00:00:00)
 */
export function getStartOfWeek(date: Date = new Date()): Date {
	const d = new Date(date);
	const day = d.getDay();
	// If Sunday (0), go back 6 days, otherwise go back (day - 1) days
	const diff = day === 0 ? 6 : day - 1;
	d.setDate(d.getDate() - diff);
	d.setHours(0, 0, 0, 0);
	return d;
}

/**
 * Calculates weekly question count (Monday to Sunday of current week)
 */
export function calculateWeeklyQuestionCount(validAttempts: QuizAttemptsResponse[]): number {
	if (!validAttempts?.length) return 0;

	const weekStart = getStartOfWeek();

	return validAttempts.reduce((sum, attempt) => {
		if (!attempt?.created) return sum;
		const createdAt = new Date(attempt.created);
		if (Number.isNaN(createdAt.getTime()) || createdAt < weekStart) return sum;
		const choices = ensureChoicesArray(attempt.choices);
		return sum + choices.length;
	}, 0);
}

/**
 * Calculates current streak (consecutive days with activity from today backwards)
 */
export function calculateStreak(validAttempts: QuizAttemptsResponse[]): number {
	if (!validAttempts?.length) return 0;

	// Get unique days with activity (sorted from newest to oldest)
	const activityDays = new Set<string>();
	validAttempts.forEach((attempt) => {
		if (!attempt?.created) return;
		const createdDate = new Date(attempt.created);
		if (Number.isNaN(createdDate.getTime())) return;

		// Use UTC date string for consistency (YYYY-MM-DD)
		const dayKey = createdDate.toISOString().split('T')[0];
		activityDays.add(dayKey);
	});

	const sortedDays = Array.from(activityDays).sort().reverse(); // From newest to oldest

	if (sortedDays.length === 0) return 0;

	// Check if the most recent day is today or yesterday
	const today = new Date().toISOString().split('T')[0];
	const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().split('T')[0];

	// If the most recent activity is not today or yesterday, streak is broken
	if (sortedDays[0] !== today && sortedDays[0] !== yesterday) {
		return 0;
	}

	let streak = 1;

	// Count consecutive days backwards from the most recent activity
	for (let i = 1; i < sortedDays.length; i++) {
		const currentDay = new Date(sortedDays[i - 1]);
		const previousDay = new Date(sortedDays[i]);

		const diffInDays = Math.round(
			(currentDay.getTime() - previousDay.getTime()) / (24 * 60 * 60 * 1000)
		);

		if (diffInDays === 1) {
			streak++;
		} else {
			break; // Streak is broken
		}
	}

	return streak;
}

/**
 * Calculates average score from recent attempts
 */
export function calculateAverageScore(
	validAttempts: QuizAttemptsResponse[],
	limit: number = 10
): number {
	if (!validAttempts?.length) return 0;

	const recent = validAttempts.slice(0, limit);
	const scores = recent.map((attempt) => {
		const choices = ensureChoicesArray(attempt.choices);
		const correct = choices.filter((c: unknown) => (c as { correct: boolean }).correct).length;
		return choices.length > 0 ? (correct / choices.length) * 100 : 0;
	});

	const avg = scores.reduce((sum, score) => sum + score, 0) / scores.length;
	return Math.round(avg);
}

/**
 * Calculates total completed quizzes
 */
export function calculateTotalQuizzes(validAttempts: QuizAttemptsResponse[]): number {
	return validAttempts?.length || 0;
}

/**
 * Calculates weekly progress percentage
 */
export function calculateWeeklyProgress(weeklyCount: number, goal: number): number {
	if (!goal) return 0;
	const percentage = Math.round((weeklyCount / goal) * 100);
	return Math.max(0, Math.min(100, percentage));
}
