import { generateId } from '$lib/utils/generate-id';
import { pb } from '$lib/pb';
import { generateUniqueTitle } from '$lib/utils/generate-unique-title';
import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
import { createAttachedFileFromMaterial } from './createAttachedFileFromMaterial';

// functions to create a new draft from an existing quiz or a blank draft
function createDraft(
	quizTemplateId?: string // if there is an ID -> we are creating a draft from an existing quiz, if there isn't -> we are creating a new blank draft,
) {
	console.log('createDraft called with quizTemplateId:', quizTemplateId);
	let currentQuiz;
	if (quizTemplateId) {
		currentQuiz = quizesStore.quizes.find((q) => q.id === quizTemplateId);
	}

	const newId = generateId();

	const formData = new FormData();
	formData.append('id', newId);
	formData.append('status', 'draft');
	formData.append('query', currentQuiz ? currentQuiz.query || '' : '');
	formData.append('materials', JSON.stringify(currentQuiz ? currentQuiz.materials || [] : []));
	formData.append('difficulty', currentQuiz ? currentQuiz.difficulty : 'intermediate');
	formData.append('itemsLimit', currentQuiz ? currentQuiz.itemsLimit.toString() : '10');
	formData.append('author', pb!.authStore.model?.id || '');
	const baseTitle = currentQuiz ? `Draft from ${currentQuiz.title}` : 'Untitled Quiz';
	const existingTitles = quizesStore.quizes.map((d) => d.title);
	const uniqueTitle = generateUniqueTitle(baseTitle, existingTitles);
	formData.append('title', uniqueTitle);
	formData.append('avoidRepeat', 'false');
	pb!.collection('quizes').create(formData);

	const attachedFiles = currentQuiz
		? currentQuiz.materials.map((materialId: string) => createAttachedFileFromMaterial(materialId))
		: [];

	return {
		id: newId,
		title: uniqueTitle,
		inputText: currentQuiz ? currentQuiz.query || '' : '',
		attachedFiles,
		selectedDifficulty: currentQuiz ? currentQuiz.difficulty : 'intermediate',
		questionCount: currentQuiz ? currentQuiz.itemsLimit : 10,
		avoidRepeat: currentQuiz ? currentQuiz.avoidRepeat : false
	};
}

export { createDraft };
