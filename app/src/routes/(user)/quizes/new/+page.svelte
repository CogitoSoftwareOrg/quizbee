<script lang="ts">
	import FileInput from './FileInput.svelte';
	import DifficultySelector from './DifficultySelector.svelte';
	import QuestionNumberSelector from './QuestionNumberSelector.svelte';
	import StartQuizButton from './StartQuizButton.svelte';
	import { tick } from 'svelte';
	import { onMount } from 'svelte';

	import Drafts from './Drafts.svelte';

	import InfoIcon from '$lib/ui/InfoIcon.svelte';
	import type { AttachedFile } from '$lib/types/attached-file';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';

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
	let showWarningLength = $state(false);

	let isDraft = $derived(
		quizesStore.quizes.find((q) => q.id === quizTemplateId)?.status === 'draft'
	);

	$effect(() => {
		if (inputElement && title) {
			inputElement.style.width = '0';
			inputElement.style.width = inputElement.scrollWidth + 5 + 'px';
		}
	});

	onMount(async () => {
		await tick();

		if (inputElement && title) {
			inputElement.style.width = '0';
			inputElement.style.width = inputElement.scrollWidth + 5 + 'px';
		}
	});
</script>

<svelte:head>
	<title>New Quiz</title>
</svelte:head>

<main class="relative flex h-full overflow-hidden">
	<Drafts
		bind:title
		bind:quizTemplateId
		bind:inputText
		bind:attachedFiles
		bind:selectedDifficulty
		bind:questionCount
		bind:isDraft
	/>

	<div class="relative flex-1 overflow-y-auto overflow-x-hidden">
		<div class="mx-auto max-w-7xl py-4 sm:px-6 lg:px-8">
			<!-- Title Section -->
			<div class="mb-12 text-center">
				<input
					bind:value={title}
					bind:this={inputElement}
					type="text"
					placeholder="Type in a title"
					class="input input-lg w-full max-w-3xl rounded-lg text-center text-3xl font-semibold sm:text-4xl lg:text-5xl"
					oninput={(e) => {
						const target = e.target as HTMLInputElement;
						const originalLength = target.value.length;
						title = target.value.slice(0, 30);
						showWarningLength = originalLength > 30;
						target.style.width = '0';
						target.style.width =
							Math.min(target.scrollWidth + 5, target.offsetParent?.clientWidth || 9999) + 'px';
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
				{#if showWarningLength}
					<p class="text-error mt-2 text-center">Title is limited to 30 characters.</p>
				{/if}
			</div>

			<!-- Describe Quiz Section -->
			<div class="mb-12 text-center">
				<div class="mb-6 flex items-center justify-center gap-2">
					<h2 class="text-2xl font-semibold sm:text-3xl lg:text-4xl">Describe your quiz</h2>
					<div
						class="tooltip tooltip-bottom [&:before]:max-w-prose [&:before]:text-balance [&:before]:text-base"
						data-tip="Describe your quiz in detail below, or simply attach files and we'll base the questions on their content. For the best results, do both!

Feel free to attach presentations, PDFs, images, and more—we support a wide range of file types. For the most accurate questions, a few focused documents are more effective than many large ones."
					>
						<InfoIcon />
					</div>
				</div>
				<div class="mx-auto w-full max-w-4xl">
					<FileInput bind:attachedFiles bind:inputText bind:quizTemplateId />
				</div>
			</div>

			<!-- Settings Section -->
			<div class="mb-16">
				<div
					class="mx-auto flex max-w-5xl flex-col items-center gap-8 lg:flex-row lg:justify-center lg:gap-16"
				>
					<!-- Difficulty -->
					<div class="w-full text-center lg:w-auto">
						<div class="mb-6 flex items-center justify-center gap-2">
							<h2 class="text-xl font-semibold sm:text-2xl">Choose difficulty level</h2>
							<div
								class="tooltip tooltip-bottom [&:before]:max-w-prose [&:before]:text-balance [&:before]:text-base"
								data-tip="Choose your level based on your knowledge of the topic. Beginner gives you simple, basic questions, while Expert challenges you with tricky, thought-provoking ones.

And don't worry, if you feel that the questions are too hard or too easy you can adjust the difficulty during the quiz!"
							>
								<InfoIcon />
							</div>
						</div>
						<DifficultySelector bind:selectedDifficulty />
					</div>

					<!-- Question Count -->
					<div class="w-full text-center lg:w-auto">
						<div class="mb-6 flex items-center justify-center gap-2">
							<h2 class="text-xl font-semibold sm:text-2xl">Choose number of questions</h2>
							<div
								class="tooltip tooltip-bottom [&:before]:max-w-prose [&:before]:text-balance [&:before]:text-base"
								data-tip="Each quiz question is a single-choice question with four answer options."
							>
								<InfoIcon />
							</div>
						</div>
						<QuestionNumberSelector bind:value={questionCount} />
					</div>
				</div>
			</div>

			<!-- Start Button -->
			<div class="flex justify-center pb-8">
				<StartQuizButton {quizTemplateId} {attachedFiles} {inputText} />
			</div>
		</div>
	</div>
</main>
