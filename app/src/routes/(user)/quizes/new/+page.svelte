<script lang="ts">
	import FileInput from './FileInput.svelte';
	import DifficultySelector from './DifficultySelector.svelte';
	import QuestionNumberSelector from './QuestionNumberSelector.svelte';
	import StartQuizButton from './StartQuizButton.svelte';
	import { tick, onMount } from 'svelte';
	import Draft from './Draft.svelte';

	import type { AttachedFile } from '$lib/types/attached-file';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { Pencil } from 'lucide-svelte';

	let quizTemplateId = $state<string>('');
	let title = $state<string>('');
	let attachedFiles = $state<AttachedFile[]>([]);
	let selectedDifficulty = $state('intermediate');
	let questionCount = $state(10);
	let inputText = $state('');
	let avoidRepeat = $state(false);

	let inputElement: HTMLInputElement;
	let showWarningLength = $state(false);

	let previousQuizes = $derived(quizesStore.quizes.filter((q: any) => q.status !== 'draft'));

	function updateInputWidth() {
		if (inputElement) {
			const viewportWidth = window.innerWidth;
			// Учитываем padding контейнера (p-4 = 1rem = ~16px с каждой стороны)
			const availableWidth = viewportWidth - 32; // 32px = padding слева и справа
			const minWidth = Math.min(viewportWidth < 640 ? 150 : 200, availableWidth * 0.6);
			const maxWidth = availableWidth * 0.95; // Максимум 95% от доступной ширины

			inputElement.style.width = '0';
			const calculatedWidth = Math.max(inputElement.scrollWidth + 5, minWidth);
			inputElement.style.width = Math.min(calculatedWidth, maxWidth) + 'px';
		}
	}

	$effect(() => {
		if (inputElement && title) {
			updateInputWidth();
		}
	});

	onMount(() => {
		tick().then(() => {
			updateInputWidth();
		});

		// Пересчитываем при изменении размера окна
		const handleResize = () => updateInputWidth();
		window.addEventListener('resize', handleResize);

		return () => {
			window.removeEventListener('resize', handleResize);
		};
	});
</script>

<svelte:head>
	<title>New Quiz</title>
</svelte:head>

<main class="relative flex h-full flex-row overflow-x-hidden">
	<div class="relative flex-1 overflow-x-hidden">
		<div class="flex items-start justify-center overflow-x-hidden">
			<div class="quiz-container w-full max-w-3xl px-4">
				<!-- Header with Title -->
				<div class="mb-9 text-center">
					<div
						class="group relative mx-auto -mt-3 inline-flex items-center justify-center gap-1 pt-2"
					>
						<input
							bind:value={title}
							bind:this={inputElement}
							type="text"
							placeholder=""
							class="hover:text-warning min-w-0 max-w-full cursor-pointer border-none bg-transparent px-0 text-center text-4xl font-bold leading-tight transition-colors focus:outline-none focus:ring-0 md:text-5xl"
							style="width: auto;"
							oninput={(e) => {
								const target = e.target as HTMLInputElement;
								const originalLength = target.value.length;
								title = target.value.slice(0, 30);
								showWarningLength = originalLength > 30;
								updateInputWidth();
							}}
							onblur={() => {
								if (title.trim() === '') {
									title = 'Untitled Quiz';
								}
							}}
						/>
						<Pencil
							class="text-base-content/40 h-6 w-6 flex-shrink-0 opacity-0 transition-opacity group-hover:opacity-100"
						/>
					</div>
					{#if showWarningLength}
						<p class="text-error -mt-1 text-center">Title is limited to 30 characters.</p>
					{:else}
						<p class="text-base-content/60 -mt-3 text-lg">
							Customize your quiz settings and get started
						</p>
						<!-- Draft Component -->
						<Draft
							bind:title
							bind:quizTemplateId
							bind:inputText
							bind:attachedFiles
							bind:selectedDifficulty
							bind:questionCount
							bind:previousQuizes
						/>
					{/if}
				</div>

				<!-- Main Card -->
				<div
					class="card bg-base-100 border-base-300 overflow-x-hidden border-2 pb-12 shadow-xl backdrop-blur-sm md:pb-0"
				>
					<div class="card-body p-6.5 overflow-x-hidden">
						<!-- Description Section -->
						<div class="mb-7">
							<div class="w-full">
								<h3 class="mb-3 block text-base font-semibold">Describe your quiz</h3>
								<FileInput bind:attachedFiles bind:inputText bind:quizTemplateId />
							</div>
						</div>

						<!-- Difficulty and Questions Grid -->
						<div class="mb-6 grid gap-6 md:grid-cols-2 md:gap-8">
							<!-- Difficulty -->
							<div>
								<h3 class="mb-4 block text-base font-semibold">Choose difficulty level</h3>
								<DifficultySelector bind:selectedDifficulty />
							</div>

							<!-- Question Count -->
							<div>
								<h3 class="mb-4 block text-base font-semibold">Number of questions</h3>
								<QuestionNumberSelector bind:value={questionCount} />
							</div>
						</div>

						<!-- Avoid Repeat Questions Section -->
						{#if previousQuizes.length > 0}
							<div class="bg-base-200/50 border-base-300 mb-5 rounded-lg border p-5">
								<div
									class="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between"
								>
									<div class="min-w-0 flex-1">
										<h3 class="mb-1 text-base font-semibold">Avoid repeating questions</h3>
										<p class="text-base-content/60 text-sm">
											We prevent questions from your previous quizzes on similar topics from
											appearing again
										</p>
									</div>
									<label class="flex flex-shrink-0 cursor-pointer items-center gap-3">
										<span
											class="label-text font-medium {avoidRepeat
												? 'text-base-content/50'
												: 'text-base-content'}">No</span
										>
										<input
											type="checkbox"
											bind:checked={avoidRepeat}
											class="toggle toggle-primary toggle-lg"
										/>
										<span
											class="label-text font-medium {avoidRepeat
												? 'text-primary'
												: 'text-base-content/50'}">Yes</span
										>
									</label>
								</div>
							</div>
						{/if}

						<!-- Start Button -->
						<StartQuizButton {quizTemplateId} {attachedFiles} {inputText} {questionCount} />
					</div>
				</div>
			</div>
		</div>
	</div>
</main>
