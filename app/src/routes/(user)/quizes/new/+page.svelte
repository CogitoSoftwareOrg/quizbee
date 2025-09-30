<script lang="ts">
	import FileInput from './FileInput.svelte';
	import DifficultySelector from './DifficultySelector.svelte';
	import QuestionNumberSelector from './QuestionNumberSelector.svelte';
	import StartQuizButton from './StartQuizButton.svelte';

	import Drafts from './Drafts.svelte';
	import { untrack } from 'svelte';
	import InfoIcon from '$lib/ui/InfoIcon.svelte';
	import type { AttachedFile } from '$lib/types/attached-file';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { pb } from '$lib/pb';
	import { generateId } from '$lib/utils/generate-id';

	function generateUniqueTitle(baseTitle: string, existingTitles: string[]): string {
		let title = baseTitle;
		let counter = 1;
		while (existingTitles.includes(title)) {
			title = `${baseTitle} (${counter})`;
			counter++;
		}
		return title;
	}

	let quizTemplateId = $state<string>('');
	let title = $state<string>('');
	let attachedFiles = $state<AttachedFile[]>([]);
	let selectedDifficulty = $state('intermediate');
	let questionCount = $state(10);
	let inputText = $state('');

	let inputElement: HTMLInputElement;

	let isDraft = $derived(
		quizesStore.quizes.find((q) => q.id === quizTemplateId)?.status === 'draft'
	);

	$effect(() => {
		if (untrack(() => quizTemplateId) && title.trim()) {
			pb!.collection('quizes').update(
				untrack(() => quizTemplateId),
				{ title: title.trim() }
			);
		}
	});

	$effect(() => {
		if (inputElement && title) {
			inputElement.style.width = '0';
			inputElement.style.width = inputElement.scrollWidth + 5 + 'px';
		}
	});
</script>

<svelte:head>
	<title>New Quiz</title>
</svelte:head>

<main class="relative flex h-full">
	<div class="flex">
		<Drafts
			bind:title
			bind:quizTemplateId
			bind:inputText
			bind:attachedFiles
			bind:selectedDifficulty
			bind:questionCount
			bind:isDraft
		/>
	</div>

	<div class="relative flex-1 overflow-y-auto py-1">
		<div class="mb-8 text-center">
			<input
				bind:value={title}
				bind:this={inputElement}
				type="text"
				placeholder="Type in a title"
				class="input input-lg rounded-lg text-center text-5xl font-semibold"
				style="min-width: 350px; min-height: 65px; padding-bottom: 5px;"
				oninput={(e) => {
					const target = e.target as HTMLInputElement;
					target.style.width = '0';
					target.style.width = target.scrollWidth + 5 + 'px';
				}}
				onblur={() => {
					if (title.trim() === '') {
						title = generateUniqueTitle(
							'Untitled',
							quizesStore.quizes.filter((q) => q.status === 'draft').map((q) => q.title)
						);
					}
				}}
			/>
		</div>

		<div class="mx-auto max-w-7xl">
			<div class="text-center">
				<div class="flex items-center justify-center gap-2">
					<h2 class="mb-1 text-4xl font-semibold">Describe your quiz</h2>
					<div
						class="tooltip tooltip-bottom -mt-1 [&:before]:max-w-[30rem] [&:before]:whitespace-pre-line [&:before]:px-6 [&:before]:py-3 [&:before]:text-left [&:before]:text-lg"
						data-tip="Describe your quiz in detail below, or simply attach files and we'll base the questions on their content. For the best results, do both!

Feel free to attach presentations, PDFs, images, and more—we support a wide range of file types. For the most accurate questions, a few focused documents are more effective than many large ones."
					>
						<InfoIcon />
					</div>
				</div>
			</div>
			<div class="mb-12 mt-4 flex justify-center">
				<div class="w-full max-w-4xl">
					<FileInput bind:attachedFiles bind:inputText bind:quizTemplateId />
				</div>
			</div>

			<div class="mb-16 flex justify-center">
				<div class="flex flex-col items-center lg:flex-row lg:items-start lg:gap-16 xl:gap-24">
					<div class="text-center">
						<div class="flex items-center justify-center gap-2">
							<h2 class="mb-6 text-2xl font-semibold">Choose difficulty level</h2>
							<div
								class="tooltip tooltip-bottom -mt-6 [&:before]:max-w-md [&:before]:whitespace-pre-line [&:before]:px-6 [&:before]:py-3 [&:before]:text-left [&:before]:text-lg"
								data-tip="Choose your level based on your knowledge of the topic. Beginner gives you simple, basic questions, while Expert challenges you with tricky, thought-provoking ones.

        And don't worry, if you feel that the questions are too hard or too easy you can adjust the difficulty during the quiz!"
							>
								<InfoIcon />
							</div>
						</div>
						<DifficultySelector bind:selectedDifficulty />
					</div>

					<div class="mt-10 text-center lg:mt-0">
						<div class="flex items-center justify-center gap-2">
							<h2 class="mb-6 text-2xl font-semibold">Choose number of questions</h2>
							<div
								class="tooltip tooltip-bottom -mt-6 [&:before]:max-w-md [&:before]:whitespace-pre-line [&:before]:px-6 [&:before]:py-3 [&:before]:text-left [&:before]:text-lg"
								data-tip="Each quiz question is a single-choice question with four answer options."
							>
								<InfoIcon />
							</div>
						</div>
						<QuestionNumberSelector bind:value={questionCount} />
					</div>
				</div>
			</div>

			<div class="flex justify-center">
				<StartQuizButton {quizTemplateId} {attachedFiles} {inputText} {selectedDifficulty} {questionCount} />
			</div>
		</div>
	</div>
</main>
