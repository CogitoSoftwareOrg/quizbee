<script lang="ts">
	import FileInput from './FileInput.svelte';
	import DifficultySelector from './DifficultySelector.svelte';
	import QuestionNumberSelector from './QuestionNumberSelector.svelte';
	import StartQuizButton from './StartQuizButton.svelte';
	import LanguageSelector from './LanguageSelector.svelte';
	import { tick, onMount } from 'svelte';
	import Draft from './Draft.svelte';

	import type { AttachedFile } from '$lib/types/attached-file';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { Pencil } from 'lucide-svelte';

	let quizTemplateId = $state<string>('');
	let title = $state<string>('');
	let attachedFiles = $state<AttachedFile[]>([]);
	let selectedDifficulty = $state('intermediate');
	let selectedLanguage = $state('English');
	let questionCount = $state(10);
	let inputText = $state('');
	let avoidRepeat = $state(false);
	let isUploading = $state(false);

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
	<!-- Use Previous Quiz Settings Button - Fixed in top right corner on desktop -->
	<div class="fixed top-2 right-4 z-50 hidden lg:block">
		<Draft
			bind:title
			bind:quizTemplateId
			bind:inputText
			bind:attachedFiles
			bind:selectedDifficulty
			bind:selectedLanguage
			bind:questionCount
			bind:previousQuizes
			bind:avoidRepeat
		/>
	</div>

	<div class="relative flex-1 overflow-x-hidden">
		<div class="flex items-start justify-center overflow-x-hidden">
			<div class="quiz-container w-full max-w-3xl px-4">
				<!-- Header with Title -->
				<div class="-mt-1 mb-2 text-center">
					<div
						class="group relative mx-auto -mt-2 inline-flex items-center justify-center gap-1 pt-2"
					>
						<input
							bind:value={title}
							bind:this={inputElement}
							type="text"
							placeholder=""
							class="-mt-2 max-w-full min-w-0 cursor-pointer border-none bg-transparent px-0 text-center text-4xl leading-tight font-bold transition-colors hover:text-warning focus:ring-0 focus:outline-none md:text-5xl"
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
						{#if title.startsWith('Untitled Quiz')}
							<Pencil class="-mt-8 ml-1 h-5 w-5 text-base-content/40" />
						{/if}
					</div>
					{#if showWarningLength}
						<p class="-mt-1 text-center text-error">Title is limited to 30 characters.</p>
					{:else}
						<p class="-mt-3 text-lg text-base-content/60">
							Customize your quiz settings and get started
						</p>
					{/if}
				</div>

				<!-- Main Card -->
				<div
					class="card overflow-x-hidden border-2 border-base-300 bg-base-100 shadow-xl backdrop-blur-sm"
				>
					<div class="card-body overflow-x-hidden px-5 py-3.5">
						<!-- Description Section -->
						<div class={previousQuizes.length === 0 ? 'mb-2' : 'mb-2'}>
							<div class="flex w-full items-start justify-between gap-3">
								<!-- <h3 class="mb-3 block text-base font-semibold">Describe your quiz</h3> -->
								<!-- Mobile Draft Button - Shows on mobile only, next to title -->
								<div class="lg:hidden">
									<Draft
										bind:title
										bind:quizTemplateId
										bind:inputText
										bind:attachedFiles
										bind:selectedDifficulty
										bind:selectedLanguage
										bind:questionCount
										bind:previousQuizes
										bind:avoidRepeat
									/>
								</div>
							</div>
							<div class="w-full">
								<FileInput
									bind:attachedFiles
									bind:inputText
									bind:quizTemplateId
									bind:isUploading
									previousQuizesLength={previousQuizes.length}
								/>
							</div>
						</div>

						<!-- Difficulty and Questions Grid -->
						<div class="mb-2 grid gap-3 md:grid-cols-2 md:gap-8">
							<!-- Difficulty -->
							<div>
								<h3 class="mb-2 block text-base font-semibold">Choose difficulty level</h3>
								<DifficultySelector bind:selectedDifficulty />
							</div>

							<!-- Question Count -->
							<div>
								<h3 class="mb-2 block text-base font-semibold">Number of questions</h3>
								<QuestionNumberSelector bind:value={questionCount} />
							</div>
						</div>

						<!-- Language -->
						<div class="mb-2">
							<h3 class="mb-2 block text-base font-semibold">Choose language of the questions</h3>
							<LanguageSelector bind:selectedLanguage />
						</div>

						<!-- Avoid Repeat Questions Section -->
						{#if previousQuizes.length > 0}
							<div class="mb-2 rounded-lg border border-base-300 bg-base-200/50 p-2.5 md:p-3.5">
								<div
									class="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between md:gap-4"
								>
									<div class="min-w-0 flex-1">
										<h3 class="mb-1 text-base font-semibold">Avoid repeating questions</h3>
										<p class="text-sm text-base-content/60">
											Prevents questions from your fully completed quizzes from appearing again.
										</p>
									</div>
									<label class="flex shrink-0 cursor-pointer items-center gap-2 md:gap-3">
										<span
											class="label-text text-base font-medium {avoidRepeat
												? 'text-base-content/50'
												: 'text-base-content'}">No</span
										>
										<div class="toggle bg-transparent! md:toggle-lg [&:before]:bg-current">
											<input type="checkbox" bind:checked={avoidRepeat} class="sr-only" />
										</div>
										<span
											class="label-text text-base font-medium {avoidRepeat
												? 'text-base-content'
												: 'text-base-content/50'}">Yes</span
										>
									</label>
								</div>
							</div>
						{/if}

						<!-- Start Button -->
						<StartQuizButton
							{quizTemplateId}
							{attachedFiles}
							{inputText}
							{questionCount}
							{isUploading}
							{selectedLanguage}
						/>
					</div>
				</div>
			</div>
		</div>
	</div>
</main>
