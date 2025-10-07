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

	let inputElement: HTMLInputElement;
	let showWarningLength = $state(false);

	let previousQuizes = $derived(quizesStore.quizes.filter((q: any) => q.status !== 'draft'));

	function updateInputWidth() {
		if (inputElement) {
			const viewportWidth = window.innerWidth;
			const minWidth = viewportWidth < 640 ? 150 : 200; // Меньше минимум на мобилке
			const maxWidth = viewportWidth * 0.9; // Максимум 90% от viewport

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

<main class="relative flex h-full flex-row overflow-hidden">
	<div class="relative flex-1 overflow-y-auto overflow-x-hidden">
		<div class="mx-auto max-w-7xl px-3 py-4 sm:px-6 lg:px-8">
			<!-- Title Section -->
			<div class="mb-6 text-center sm:mb-12">
				<div class="relative mx-auto inline-flex min-w-0 items-center justify-center">
					<input
						bind:value={title}
						bind:this={inputElement}
						type="text"
						placeholder=""
						class={[
							'input input-xl min-w-0 rounded-lg border-2 pt-3 text-center font-semibold',
							'text-2xl sm:text-3xl md:text-4xl lg:text-5xl',
							title === 'Untitled Quiz' ? 'pr-8' : ''
						].join(' ')}
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
					{#if title === 'Untitled Quiz'}
						<div
							class="-translate-y-3/5 pointer-events-none absolute left-1/2 top-0"
							style="transform: translateX(calc({title.length *
								1}ch - 50% + 2ch)) translateY(-60%);"
						>
							<Pencil class="text-base-content/30 size-4" />
						</div>
					{/if}
				</div>
				{#if showWarningLength}
					<p class="text-error mt-2 text-center">Title is limited to 30 characters.</p>
				{/if}
			</div>

			<!-- Describe Quiz Section -->
			<div class="mb-6 text-center sm:mb-12">
				<div class="mb-3 flex items-center justify-center gap-2 px-2 sm:mb-4">
					<h2 class="text-lg font-semibold sm:text-xl md:text-2xl lg:text-3xl">
						Describe your quiz
					</h2>
				</div>

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

				<div class="mx-auto w-full max-w-4xl">
					<FileInput bind:attachedFiles bind:inputText bind:quizTemplateId />
				</div>
			</div>

			<!-- Settings Section -->
			<div class="mb-8 sm:mb-16">
				<div
					class="mx-auto flex max-w-7xl flex-col items-center gap-6 sm:gap-12 lg:flex-row lg:justify-center lg:gap-16"
				>
					<!-- Difficulty -->
					<div class="w-full min-w-0 flex-1 text-center lg:w-auto">
						<div class="mb-3 flex items-center justify-center gap-2 px-2 sm:mb-6">
							<h2 class="text-sm font-semibold sm:text-base md:text-lg lg:text-xl">
								Difficulty level
							</h2>
						</div>
						<DifficultySelector bind:selectedDifficulty />
					</div>

					<!-- Question Count -->
					<div class="w-full min-w-0 flex-1 text-center lg:w-auto">
						<div class="mb-3 flex items-center justify-center gap-2 px-2 sm:mb-6">
							<h2 class="text-sm font-semibold sm:text-base md:text-lg lg:text-xl">
								Number of questions
							</h2>
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
