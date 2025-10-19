<script lang="ts">
	import { onMount } from 'svelte';

	// import { TextArea } from '@cogisoft/ui-svelte-daisy';

	import { computeApiUrl } from '$lib/api/compute-url';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import type { AttachedFile } from '$lib/types/attached-file';
	import { pb } from '$lib/pb';
	import type { MaterialsResponse } from '$lib/pb/pocketbase-types';
	import { generateId } from '$lib/utils/generate-id';
	import { removeFile } from '../new/removeFile';
	import { addExistingMaterial } from '../new/addExistingMaterial';

	interface Props {
		inputText: string;
		attachedFiles: AttachedFile[];
		quizTemplateId?: string;
	}

	let {
		inputText = $bindable(''),
		attachedFiles = $bindable([]),
		quizTemplateId = $bindable('')
	}: Props = $props();

	const maxTokensWithABook = 400000;
	const maxTokensWithoutABook = 160000;

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
	let warningMaxTokensExceeded = $derived(
		attachedFiles.length >= 2 &&
			(hasBook ? totalTokensAttached > maxTokensWithABook : totalTokensAttached > maxTokensWithoutABook)
	);

	let buttonElement = $state<HTMLButtonElement>();
	let menuElement = $state<HTMLDivElement>();

	const allowedExtensions = [
		'pdf',
		'md',
		'txt',
		'js',
		'ts',
		'html',
		'css',
		'json',
		'xml',
		'svg',
		'jpg',
		'jpeg',
		'png',
	];
	onMount(() => {
		document.addEventListener('click', handleClickOutside);

		return () => {
			document.removeEventListener('click', handleClickOutside);

			// Освобождаем все URL превью
			attachedFiles.forEach((attachedFile) => {
				if (attachedFile.previewUrl) {
					URL.revokeObjectURL(attachedFile.previewUrl);
				}
			});
		};
	});

	function processFiles(files: File[]) {
		for (const file of files) {
			const extension = file.name.split('.').pop()?.toLowerCase();
			if (!extension || !allowedExtensions.includes(extension)) {
				warningUnsupportedFile = file.name;
				setTimeout(() => {
					warningUnsupportedFile = null;
				}, 5000);
				continue;
			}

			const attachedFile: AttachedFile = {
				file,
				previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : null,
				name: file.name,
				isUploading: true,
				materialId: generateId()
			};

			attachedFiles = [...attachedFiles, attachedFile];
			uploadFileAsync(attachedFile);
		}
	}

	// Для материалов которые сейчас грузим реактивно отслеживаем материалы в store и обновляем статус загрузки
	$effect(() => {
		// Обход с конца, чтобы безопасно удалять элементы
		for (let i = attachedFiles.length - 1; i >= 0; i--) {
			const attachedFile = attachedFiles[i];
			if (attachedFile.isUploading && attachedFile.materialId) {
				const foundMaterial = materialsStore.materials.find(
					(m) => m.id === attachedFile.materialId
				);

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
					} else if (foundMaterial.status === 'uploaded') {
						attachedFile.tokens = foundMaterial.tokens;
						attachedFile.isBook = foundMaterial.isBook;
						attachedFile.isUploading = false;
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
			processFiles(Array.from(target.files));
		}
	}

	// Асинхронная загрузка файла
	async function uploadFileAsync(attachedFile: AttachedFile) {
		try {
			const formData = new FormData();
			formData.append('file', attachedFile.file!);
			formData.append('title', attachedFile.name);
			formData.append('material_id', attachedFile.materialId!);

			const response = await fetch(`${computeApiUrl()}materials/upload`, {
				method: 'POST',
				body: formData,
				credentials: 'include'
			});

			if (!response.ok) {
				const errorText = await response.text();
				throw new Error(`Failed to upload material: ${errorText}`);
			}

			const material = await response.json();

			attachedFile.materialId = material.id;

			if (material.tokens) {
				attachedFile.tokens = material.tokens;
			}

			try {
				await pb!
					.collection('quizes')
					.update(quizTemplateId, { 'materials+': material.id }, { requestKey: material.id });
			} catch (error) {
				console.error('Failed to attach material to quiz:', error);
			}
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
			processFiles(files);
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
			processFiles(Array.from(files));
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

		const iconMap: Record<string, string> = {
			pdf: 'pdf',
			md: 'md',
			txt: 'txt',
			js: 'js',
			ts: 'js',
			html: 'html',
			css: 'css',
			json: 'json',
			
			
		};

		return iconMap[extension || ''] || 'unknown';
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
		'flex w-full flex-col gap-2.5 rounded-lg font-sans transition-colors duration-200',
		isDragging && 'border-primary bg-primary/10 border-2 border-dashed'
	]}
	ondragover={handleDragOver}
	ondragleave={handleDragLeave}
	ondrop={handleDrop}
	role="button"
	tabindex="0"
	aria-label="Drop files here or click to upload"
>
	<div
		class="border-base-300 bg-base-300 focus-within:border-base-content/40 relative flex items-center rounded-3xl border px-3 py-3 transition-colors duration-200 sm:px-4 sm:py-4"
	>
		<button
			bind:this={buttonElement}
			onclick={() => (isMaterialsListOpen = !isMaterialsListOpen)}
			class="text-base-content/60 hover:text-base-content mr-2 flex shrink-0 cursor-pointer items-center border-none bg-transparent p-0"
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
				class="border-base-300 bg-base-100 absolute left-0 right-0 top-full z-10 mt-2 max-h-[70vh] overflow-y-auto rounded-lg border shadow-lg sm:left-0 sm:right-auto sm:w-80"
			>
				<div class="p-2">
					<button
						onclick={() => {
							openFileDialog();
							isMaterialsListOpen = false;
						}}
						class="btn btn-warning flex w-full items-center gap-2 text-left text-lg"
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
				<div class="border-base-300 border-t p-2">
					<div class="text-base-content/70 mb-2 text-center text-lg font-medium">
						Previous Materials
					</div>
					<div class="relative">
						<input
							bind:value={searchQuery}
							placeholder="Search materials..."
							class="border-base-300 focus:border-primary w-full rounded border py-1 pl-8 pr-2 text-sm focus:outline-none"
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
							class="lucide lucide-search text-base-content/60 absolute left-2 top-1/2 -translate-y-1/2 transform"
							><circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" /></svg
						>
					</div>
					<div class="max-h-67 mt-2">
						{#each materialsStore.materials.filter((m) => m.title
								.toLowerCase()
								.includes(searchQuery.toLowerCase())) as material}
							<button
								class="hover:bg-primary flex w-full cursor-pointer items-center justify-between gap-2 p-2 text-left transition-colors duration-200"
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
										class="lucide lucide-check flex-shrink-0"
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
			placeholder="Attach relevant files and/or describe what you'd like the questions to be about"
			bind:value={inputText}
			class="max-h-[7.5rem] min-h-[1.5rem] flex-grow resize-none border-none bg-transparent py-1 pl-4 text-lg leading-6 outline-none focus:shadow-none focus:outline-none focus:ring-0"
			onpaste={handlePaste}
			rows="1"
			oninput={handleTextareaResize}
		></textarea>
		<!-- <TextArea
			bind:value={inputText}
			placeholder="Attach relevant files and/or describe what you'd like the questions to be about"
			onpaste={handlePaste}
			oninput={handleTextareaResize}
		></TextArea> -->
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
			File "{warningTooBigFile}" is too big and cannot be uploaded.
		</div>
	{/if}
	{#if warningUnsupportedFile}
		<div class="text-md mt-2 text-red-500">
			File "{warningUnsupportedFile}" has an unsupported format and cannot be uploaded.
		</div>
	{/if}
	{#if warningMaxTokensExceeded}
		<div class="text-md mt-2 text-orange-500">
			You have attached too much material. You can still start the quiz, but the quality may be
			degraded.
		</div>
	{/if}
	{#if attachedFiles.length > 0}
		<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
			{#each attachedFiles as attachedFile, index}
				<div class="bg-base-300 group relative aspect-square w-full rounded-lg">
					{#if attachedFile.previewUrl}
						<img
							src={attachedFile.previewUrl}
							alt={attachedFile.name}
							class="h-full w-full object-cover"
						/>
					{:else}
						<div
							class="text-base-content/60 flex h-full w-full flex-col items-center gap-5 p-2 text-center"
						>
							<img
								src="/file-format-icons/{getFileIcon(attachedFile.name)}.svg"
								alt="File icon"
								class="file-icon h-10 w-10"
							/>
							<span
								class="line-clamp-3 break-all text-[14px] leading-tight"
								title={attachedFile.name}>{attachedFile.name}</span
							>
						</div>
					{/if}

					<!-- Индикатор загрузки -->
					{#if attachedFile.isUploading}
						<div class="bg-base-content/50 absolute inset-0 flex items-center justify-center">
							<div
								class="border-base-100 h-8 w-8 animate-spin rounded-full border-4 border-t-transparent"
							></div>
						</div>
					{/if}

					<button
						onclick={async () => {
							attachedFiles = await removeFile(index, attachedFiles, quizTemplateId);
						}}
						class="bg-base-content/50 text-base-100 absolute right-1 top-1 flex h-5 w-5 cursor-pointer items-center justify-center rounded-full border-none text-sm leading-none opacity-0 transition-opacity group-hover:opacity-100"
						aria-label="Remove file">&times;</button
					>
				</div>
			{/each}
		</div>
	{/if}
</div>
