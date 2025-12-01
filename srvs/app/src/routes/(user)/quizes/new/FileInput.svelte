<script lang="ts">
	import { onMount } from 'svelte';
	import posthog from 'posthog-js';

	// import { TextArea } from '@quizbee/ui-svelte-daisy';
	import type { MaterialsResponse } from '@quizbee/pb-types';

	import { computeApiUrl } from '$lib/api/compute-url';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import type { AttachedFile } from '$lib/types/attached-file';
	import { pb } from '$lib/pb';
	import { generateId } from '$lib/utils/generate-id';
	import { computeFileHash } from '$lib/utils/file-hash';
	import { removeFile } from '../new/removeFile';
	import { addExistingMaterial } from '../new/addExistingMaterial';
	import PreviousQuizes from './PreviousQuizes.svelte';
	import { postApi } from '$lib/api/call-api';

	interface Props {
		inputText: string;
		attachedFiles: AttachedFile[];
		quizTemplateId?: string;
		previousQuizesLength: number;
		isUploading?: boolean;
	}

	let {
		inputText = $bindable(''),
		attachedFiles = $bindable([]),
		quizTemplateId = $bindable(''),
		previousQuizesLength = 0,
		isUploading = $bindable(false)
	}: Props = $props();

	const maxTokensWithABook = 450000;
	const maxTokensWithoutABook = 180000;

	const totalTokensAttached = $derived(
		attachedFiles.reduce((sum, file) => sum + (file.tokens || 0), 0)
	);

	const hasBook = $derived(attachedFiles.some((file) => file.isBook));

	let inputElement: HTMLInputElement;
	let isDragging = $state(false);
	let isMaterialsListOpen = $state(false);
	let searchQuery = $state('');
	let warningTooBigQuery = $state(false);
	let warningTooBigFile = $state<string | null>(null);
	let warningUnsupportedFile = $state<string | null>(null);
	let warningNoText = $state<string | null>(null);
	let warningTotalSizeExceeded = $state<string | null>(null);

	const MAX_TOTAL_SIZE = 76 * 1024 * 1024;
	const totalSizeAttached = $derived(
		attachedFiles.reduce((sum, file) => sum + (file.size || 0), 0)
	);

	let warningMaxTokensExceeded = $derived(
		attachedFiles.length >= 2 &&
			(hasBook
				? totalTokensAttached > maxTokensWithABook
				: totalTokensAttached > maxTokensWithoutABook)
	);

	let warningLargeFileProcessing = $derived(
		attachedFiles.some((f) => f.file && f.file.size > 15 * 1024 * 1024 && f.isUploading)
	);

	let placeholderText = $state('Attach files • Add text');

	let buttonElement = $state<HTMLButtonElement>();
	let menuElement = $state<HTMLDivElement>();

	const allowedExtensions = ['pdf', 'pptx', 'docx', 'md', 'txt', 'html', 'xlsx', 'csv'];

	// Track if any files are currently uploading
	$effect(() => {
		isUploading = attachedFiles.some((file) => file.isUploading);
	});

	onMount(() => {
		document.addEventListener('click', handleClickOutside);

		// пофиксить эту хуйню потом
		const updatePlaceholder = () => {
			placeholderText =
				window.innerWidth >= 768
					? 'Attach study materials you want to make quiz from • Add text instructions'
					: 'Attach files • Add text';
		};

		updatePlaceholder();
		window.addEventListener('resize', updatePlaceholder);

		return () => {
			document.removeEventListener('click', handleClickOutside);
			window.removeEventListener('resize', updatePlaceholder);

			// Освобождаем все URL превью
			attachedFiles.forEach((attachedFile) => {
				if (attachedFile.previewUrl) {
					URL.revokeObjectURL(attachedFile.previewUrl);
				}
			});
		};
	});

	// первая функция которая дергается когда в проводнике мы выбираем файлы
	async function processFiles(files: File[]) {
		const MAX_CONCURRENT_UPLOADS = 10; // Ограничиваем параллелизм, чтобы избежать проблем с PocketBase POST trigger
		const validFiles: File[] = [];

		// Сначала валидируем все файлы
		for (const file of files) {
			const extension = file.name.split('.').pop()?.toLowerCase();
			if (!extension || !allowedExtensions.includes(extension)) {
				warningUnsupportedFile = file.name;
				setTimeout(() => {
					warningUnsupportedFile = null;
				}, 5000);
				continue;
			}

			// Check file size (100MB limit)
			if (file.size > 1024 * 1024 * 75) {
				warningTooBigFile = file.name;
				setTimeout(() => {
					warningTooBigFile = null;
				}, 5000);
				continue;
			}

			const currentTotalSize = attachedFiles.reduce((sum, f) => sum + (f.size || 0), 0);
			const pendingFilesSize = validFiles.reduce((sum, f) => sum + f.size, 0);
			if (currentTotalSize + pendingFilesSize + file.size > MAX_TOTAL_SIZE) {
				warningTotalSizeExceeded = file.name;
				setTimeout(() => {
					warningTotalSizeExceeded = null;
				}, 5000);
				continue;
			}

			validFiles.push(file);
		}

		// Загружаем файлы с ограниченным параллелизмом
		for (let i = 0; i < validFiles.length; i += MAX_CONCURRENT_UPLOADS) {
			const batch = validFiles.slice(i, i + MAX_CONCURRENT_UPLOADS);
			const attachedFilesBatch: AttachedFile[] = batch.map((file) => ({
				file,
				previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : null,
				name: file.name,
				isUploading: true,
				isHashing: true,
				materialId: generateId(),
				size: file.size
			}));

			attachedFiles = [...attachedFiles, ...attachedFilesBatch];

			// Обрабатываем файлы последовательно чтобы избежать race condition при модификации attachedFiles
			for (const attachedFile of attachedFilesBatch) {
				await uploadFileAsync(attachedFile);
			}
		}
	}

	// Для материалов которые сейчас грузим реактивно отслеживаем материалы в store и обновляем статус загрузки
	$effect(() => {
		// Обход с конца, чтобы безопасно удалять элементы
		for (let i = attachedFiles.length - 1; i >= 0; i--) {
			const attachedFile = attachedFiles[i];
			console.log(
				'$effect checking file:',
				attachedFile.name,
				'isUploading:',
				attachedFile.isUploading,
				'materialId:',
				attachedFile.materialId
			);
			if (attachedFile.isUploading && attachedFile.materialId) {
				const foundMaterial = materialsStore.materials.find(
					(m) => m.id === attachedFile.materialId
				);
				console.log('foundMaterial:', foundMaterial);

				if (foundMaterial) {
					// Check if file is too big
					if (foundMaterial.status === 'too big') {
						warningTooBigFile = attachedFile.name;
						// Remove the file from attachedFiles
						removeFile(i, attachedFiles, quizTemplateId);
						// Clear warning after 5 seconds
						setTimeout(() => {
							warningTooBigFile = null;
						}, 5000);
					} else if ((foundMaterial.status as string) === 'no text') {
						warningNoText = attachedFile.name;
						// Remove the file from attachedFiles
						removeFile(i, attachedFiles, quizTemplateId);
						// Clear warning after 5 seconds
						setTimeout(() => {
							warningNoText = null;
						}, 5000);
					} else if (foundMaterial.status === 'indexing') {
						attachedFile.isIndexing = true;
					} else if (foundMaterial.status === 'indexed') {
						attachedFile.tokens = foundMaterial.tokens;
						attachedFile.isBook = foundMaterial.isBook;
						attachedFile.isUploading = false;
						attachedFile.isIndexing = false;
					}
				}
			}
		}
	});

	function openFileDialog() {
		inputElement.click();
	}

	async function handleFileChange(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files) {
			await processFiles(Array.from(target.files));
		}
	}

	// Асинхронная загрузка файла (эта функция вызывается из processFiles)
	async function uploadFileAsync(attachedFile: AttachedFile) {
		console.log('uploadFileAsync called with attachedFile:', attachedFile);
		try {
			const hash = await computeFileHash(attachedFile.file!);
			attachedFile.hash = hash;
			attachedFile.isHashing = false;
			attachedFiles = attachedFiles;

			const existingMaterial = materialsStore.materials.find((m) => m.hash === hash);
			console.log('Hash computed:', hash, 'existingMaterial:', existingMaterial);
			if (existingMaterial) {
				console.log('Found duplicate! Reusing existing material');
				const fileIndex = attachedFiles.findIndex((f) => f.materialId === attachedFile.materialId);
				console.log('fileIndex:', fileIndex);
				if (fileIndex !== -1) {
					if (attachedFile.previewUrl) {
						URL.revokeObjectURL(attachedFile.previewUrl);
					}

					const material = materialsStore.materials.find((m) => m.id === existingMaterial.id);

					attachedFiles[fileIndex].name = material!.title;
					attachedFiles[fileIndex].isUploading = false;
					attachedFiles[fileIndex].isIndexing = false;
					attachedFiles[fileIndex].materialId = material!.id;
					attachedFiles[fileIndex].tokens = material!.tokens || 0;
					attachedFiles[fileIndex].isBook = material!.isBook || false;
					attachedFiles[fileIndex].previewUrl =
						material!.file && /\.(jpg|jpeg|png|gif|webp)$/i.test(material!.file)
							? pb!.files.getURL(material!, material!.file)
							: null;

					if (quizTemplateId) {
						try {
							const quiz = await pb!.collection('quizes').getOne(quizTemplateId);
							const updatedMaterials = [...(quiz.materials || []), material!.id];
							await pb!
								.collection('quizes')
								.update(quizTemplateId, { materials: updatedMaterials });
						} catch (error) {
							console.error('Failed to attach material to quiz:', error);
						}
					}

					attachedFiles = attachedFiles;
					console.log('Updated attachedFile:', attachedFiles[fileIndex]);
				}
				return;
			}

			const formData = new FormData();
			formData.append('file', attachedFile.file!);
			formData.append('title', attachedFile.name);
			formData.append('material_id', attachedFile.materialId!);
			formData.append('hash', hash);

			if (quizTemplateId) formData.append('quiz_id', quizTemplateId);

			const response = await fetch(`${computeApiUrl()}materials`, {
				method: 'POST',
				body: formData,
				credentials: 'include'
			});

			if (!response.ok) {
				const errorText = await response.text();
				throw new Error(`Failed to upload material: ${errorText}`);
			}

			posthog.capture('file_attached', {
				quizTemplateId: quizTemplateId || null
			});
		} catch (error) {
			console.error('Failed to upload file:', attachedFile.name, error);
			// Находим индекс файла в массиве и удаляем его
			const fileIndex = attachedFiles.indexOf(attachedFile);
			if (fileIndex !== -1) {
				// Освобождаем URL превью если есть
				if (attachedFile.previewUrl) {
					URL.revokeObjectURL(attachedFile.previewUrl);
				}
				attachedFiles.splice(fileIndex, 1);
				attachedFiles = attachedFiles;
			}
		}
	}

	async function toggleMaterial(material: MaterialsResponse) {
		const existingIndex = attachedFiles.findIndex((file) => file.materialId === material.id);
		if (existingIndex !== -1) {
			// Материал уже прикреплен - удаляем его
			attachedFiles = await removeFile(existingIndex, attachedFiles, quizTemplateId);
		} else {
			// Материал не прикреплен - добавляем его
			const attachedFile = await addExistingMaterial(material.id, quizTemplateId);
			attachedFiles = [...attachedFiles, attachedFile];
		}
	}

	function isMaterialAttached(materialId: string): boolean {
		return attachedFiles.some((file) => file.materialId === materialId);
	}

	async function handlePaste(event: ClipboardEvent) {
		const clipboardData = event.clipboardData;
		if (!clipboardData) return;

		const items = Array.from(clipboardData.items);
		const imageItems = items.filter((item) => item.type.startsWith('image/'));

		if (imageItems.length > 0) {
			event.preventDefault();
			const files = imageItems
				.map((item) => item.getAsFile())
				.filter((file) => file !== null) as File[];
			await processFiles(files);
		}
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		isDragging = true;
	}

	function handleDragLeave(event: DragEvent) {
		event.preventDefault();
		isDragging = false;
	}

	async function handleDrop(event: DragEvent) {
		event.preventDefault();
		isDragging = false;

		const files = event.dataTransfer?.files;
		if (files) {
			await processFiles(Array.from(files));
		}
	}

	function handleTextareaResize(event: Event) {
		const target = event.target as HTMLTextAreaElement;
		target.style.height = 'auto';
		const scrollHeight = target.scrollHeight;
		const maxHeight = 7.5 * 16;
		target.style.height = Math.min(scrollHeight, maxHeight) + 'px';

		if (target.value.length > 100000) {
			target.value = target.value.slice(0, 100000);
			inputText = target.value;
			warningTooBigQuery = true;
		} else {
			warningTooBigQuery = false;
		}
	}

	function getFileIcon(filename: string): string {
		const extension = filename.split('.').pop()?.toLowerCase();

		return extension || '';
	}

	function truncateFileName(filename: string, maxLength: number = 50): string {
		if (filename.length <= maxLength) {
			return filename;
		}
		return filename.substring(0, maxLength - 3) + '...';
	}

	function handleClickOutside(event: MouseEvent) {
		if (
			menuElement &&
			!menuElement.contains(event.target as Node) &&
			buttonElement &&
			!buttonElement.contains(event.target as Node)
		) {
			isMaterialsListOpen = false;
		}
	}

	export { addExistingMaterial };
</script>

<div
	class={[
		'flex w-full flex-col gap-2 rounded-lg font-sans transition-colors duration-200',
		isDragging && 'border-2 border-dashed border-primary bg-primary/10'
	]}
	ondragover={handleDragOver}
	ondragleave={handleDragLeave}
	ondrop={handleDrop}
	role="button"
	tabindex="0"
	aria-label="Drop files here or click to upload"
>
	<div
		class="relative flex items-center rounded-3xl border border-base-300 bg-base-300 px-3 py-3 transition-colors duration-200 focus-within:border-base-content/40 sm:px-4 sm:py-4"
	>
		<button
			bind:this={buttonElement}
			onclick={() => (isMaterialsListOpen = !isMaterialsListOpen)}
			class="mr-2 flex shrink-0 cursor-pointer items-center border-none bg-transparent p-0 text-base-content/60 hover:text-base-content"
			aria-label="Attach files"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="20"
				height="20"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
				class="lucide lucide-paperclip sm:h-6 sm:w-6"
				><path
					d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.59a2 2 0 0 1-2.83-2.83l8.49-8.48"
				/></svg
			>
		</button>
		{#if isMaterialsListOpen}
			<div
				bind:this={menuElement}
				class="absolute top-full right-0 left-0 z-10 mt-2 max-h-[70vh] overflow-y-auto rounded-lg border-2 border-base-300 bg-base-100 shadow-xl sm:right-auto sm:left-0 sm:w-80"
			>
				<div class="p-4">
					<button
						onclick={() => {
							openFileDialog();
							isMaterialsListOpen = false;
						}}
						class="btn flex w-full items-center gap-2 text-left text-lg btn-warning"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="16"
							height="16"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="3"
							stroke-linecap="round"
							stroke-linejoin="round"
							class="lucide lucide-plus"><path d="M12 5v14M5 12h14" /></svg
						>
						<span class="mt-1">Add Files from PC</span>
					</button>
				</div>
				<div class="border-t border-base-300 p-3">
					<div class="mb-2 text-center text-lg font-medium text-base-content/70">
						Previous Materials
					</div>
					<div class="relative">
						<input
							bind:value={searchQuery}
							placeholder="Search materials..."
							class="w-full rounded border border-base-300 py-2 pr-2 pl-8 text-sm focus:border-primary focus:outline-none"
						/>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="16"
							height="16"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
							class="lucide lucide-search absolute top-1/2 left-2 -translate-y-1/2 transform text-base-content/60"
							><circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" /></svg
						>
					</div>
					<div class="mt-2 max-h-67">
						{#each materialsStore.materials.filter((m) => (m.status === 'indexed' || m.status === 'used') && m.title
									.toLowerCase()
									.includes(searchQuery.toLowerCase())) as material}
							<button
								class="flex w-full cursor-pointer items-center justify-between gap-2 rounded p-3 text-left transition-colors duration-200 hover:bg-primary"
								onclick={() => {
									toggleMaterial(material);
								}}
							>
								<span class="flex-1 truncate">{material.title}</span>
								{#if isMaterialAttached(material.id)}
									<svg
										xmlns="http://www.w3.org/2000/svg"
										width="20"
										height="20"
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="2"
										stroke-linecap="round"
										stroke-linejoin="round"
										class="lucide lucide-check shrink-0"
									>
										<path d="M20 6 9 17l-5-5" />
									</svg>
								{/if}
							</button>
						{/each}
					</div>
				</div>
			</div>
		{/if}
		<textarea
			placeholder={placeholderText}
			bind:value={inputText}
			class="max-h-[4.5rem] flex-grow resize-none overflow-y-auto border-none bg-transparent py-0 pl-4 text-lg leading-6 outline-none focus:shadow-none focus:ring-0 focus:outline-none"
			onpaste={handlePaste}
			rows="1"
			oninput={handleTextareaResize}
		></textarea>

		<input
			type="file"
			bind:this={inputElement}
			onchange={handleFileChange}
			multiple
			style="display: none;"
		/>
	</div>
	{#if warningTooBigQuery}
		<div class="text-md mt-2 text-red-500">Maximum input length is 100.000 symbols.</div>
	{/if}
	{#if warningTooBigFile}
		<div class="text-md mt-2 text-red-500">
			File "{warningTooBigFile}" is too big and cannot be uploaded. Maximum file size is 75MB.
		</div>
	{/if}
	{#if warningTotalSizeExceeded}
		<div class="text-md mt-2 text-red-500">
			File "{warningTotalSizeExceeded}" cannot be attached. Total size of all files cannot exceed
			75MB. Please consider starting several quizzes with fewer materials.
		</div>
	{/if}
	{#if warningNoText}
		<div class="text-md mt-2 text-red-500">
			We can't process material "{warningNoText}" as it has no or very little text.
		</div>
	{/if}
	{#if warningUnsupportedFile}
		<div class="text-md mt-2 text-red-500">
			File "{warningUnsupportedFile}" has an unsupported format and cannot be uploaded. We support
			PDF, PPTX, DOCX and text based formats (MD, TXT, HTML, CSV).
		</div>
	{/if}
	{#if warningMaxTokensExceeded}
		<div class="text-md mt-2 text-orange-500">
			You have attached too much material. You can still start the quiz, but the quality may be
			degraded.
		</div>
	{/if}
	{#if warningLargeFileProcessing}
		<div class="text-md mt-2 text-orange-500">
			You've attached a large file and the processing may take up to a few minutes. Please be
			patient, you can reuse the material in other quizzes after it is processed.
		</div>
	{/if}
	{#if attachedFiles.length > 0}
		<div class="flex gap-3 overflow-x-auto px-1 pb-2" style="scrollbar-width: auto;">
			{#each attachedFiles as attachedFile, index}
				<div
					class="group relative mb-0.5 aspect-square h-24 w-24 shrink-0 rounded-lg border-2 border-base-content/20 bg-base-300 p-1.5"
				>
					{#if attachedFile.previewUrl}
						<img
							src={attachedFile.previewUrl}
							alt={attachedFile.name}
							class="h-full w-full rounded object-cover"
						/>
					{:else}
						<div class="flex flex-col items-center gap-5 text-center text-base-content/60">
							<img
								src="/file-format-icons/{getFileIcon(attachedFile.name)}.svg"
								alt="File icon"
								class="file-icon h-8 w-8"
							/>
							<span
								class="-mt-2 line-clamp-3 text-[0.7rem] leading-tight break-all"
								title={attachedFile.name}>{attachedFile.name}</span
							>
						</div>
					{/if}

					<!-- Индикатор загрузки -->
					{#if attachedFile.isUploading}
						<div
							class="absolute inset-0 flex flex-col items-center justify-center bg-base-content/50"
						>
							<div
								class="h-8 w-8 animate-spin rounded-full border-4 border-base-100 border-t-transparent"
							></div>
							{#if attachedFile.isIndexing}
								<span class="text-md mt-1 font-bold text-base-100">Indexing</span>
							{/if}
						</div>
					{/if}

					<button
						onclick={async () => {
							attachedFiles = await removeFile(index, attachedFiles, quizTemplateId);
						}}
						class="ы absolute top-1 right-1 flex h-5 w-5 cursor-pointer items-center justify-center border-none text-xl text-base-content"
						aria-label="Remove file">&times;</button
					>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- max-height handled via Tailwind classes: `max-h-[55px] xxl:max-h-[70px]` -->
