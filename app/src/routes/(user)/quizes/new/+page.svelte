<script lang="ts">
	import FileInput from './FileInput.svelte';
	import DifficultySelector from './DifficultySelector.svelte';
	import QuestionNumberSelector from './QuestionNumberSelector.svelte';
	import StartQuizButton from './StartQuizButton.svelte';
	import PreviousQuizes from './PreviousQuizes.svelte';
	import type { AttachedFile } from '$lib/types/attached-file';

	let attachedFiles = $state<AttachedFile[]>([]);
	let selectedDifficulty = $state('intermediate');
	let questionCount = $state(10);
	let inputText = $state('');
</script>

<svelte:head>
	<title>New Quiz</title>
</svelte:head>

<main class="relative flex h-full">
	<PreviousQuizes bind:inputText bind:attachedFiles />

	<div class="relative flex-1 overflow-y-auto px-8 py-16">
		<div class="mb-12 text-center">
			<h1 class="text-5xl font-bold">New Quiz</h1>
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
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="28"
							height="28"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
							class="cursor-pointer text-gray-500 transition-colors duration-200 hover:text-gray-700"
						>
							<circle cx="12" cy="12" r="10" />
							<path d="M12 16v-4" />
							<path d="M12 8h.01" />
						</svg>
					</div>
				</div>
			</div>
			<div class="mb-12 mt-4 flex justify-center">
				<div class="w-full max-w-4xl">
					<FileInput bind:attachedFiles bind:inputText />
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
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="28"
									height="28"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
									class="cursor-pointer text-gray-500 transition-colors duration-200 hover:text-gray-700"
								>
									<circle cx="12" cy="12" r="10" />
									<path d="M12 16v-4" />
									<path d="M12 8h.01" />
								</svg>
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
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="28"
									height="28"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
									class="cursor-pointer text-gray-500 transition-colors duration-200 hover:text-gray-700"
								>
									<circle cx="12" cy="12" r="10" />
									<path d="M12 16v-4" />
									<path d="M12 8h.01" />
								</svg>
							</div>
						</div>
						<QuestionNumberSelector bind:value={questionCount} />
					</div>
				</div>
			</div>

			<div class="flex justify-center">
				<StartQuizButton {attachedFiles} {inputText} {selectedDifficulty} {questionCount} />
			</div>
		</div>
	</div>
</main>

<style>
	:global(*) {
		scrollbar-width: none !important;
		-ms-overflow-style: none !important;
	}

	:global(*::-webkit-scrollbar) {
		display: none !important;
	}
</style>
