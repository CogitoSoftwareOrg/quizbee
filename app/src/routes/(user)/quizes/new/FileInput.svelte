<script lang="ts">
	import { onMount } from 'svelte';
	import { computeApiUrl } from '$lib/api/compute-url';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import type { AttachedFile } from '$lib/types/attached-file';
	import { pb } from '$lib/pb';
	import type { MaterialsResponse } from '$lib/pb/pocketbase-types';
	import { generateId } from '$lib/utils/generate-id';

	interface Props {
		inputText?: string;
		attachedFiles?: AttachedFile[];
		quizTemplateId?: string;
	}

	let {
		inputText = $bindable(''),
		attachedFiles = $bindable([]),
		quizTemplateId = $bindable('')
	}: Props = $props();

	let inputElement: HTMLInputElement;
	let isDragging = $state(false);
	let isMaterialsListOpen = $state(false);
	let searchQuery = $state('');
	let warningTextInput = $state(false);

	let buttonElement = $state<HTMLButtonElement>();
	let menuElement = $state<HTMLDivElement>();

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
		attachedFiles.forEach((attachedFile) => {
			if (attachedFile.isUploading && attachedFile.materialId) {
				const foundMaterial = materialsStore.materials.find(
					(m) => m.id === attachedFile.materialId
				);

				if (foundMaterial) {
					attachedFile.isUploading = false;
				}
			}
		});
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
				const quiz = await pb!.collection('quizes').getOne(quizTemplateId);
				const updatedMaterials = [...(quiz.materials || []), material.id];
				await pb!.collection('quizes').update(quizTemplateId, { materials: updatedMaterials });
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

	// Добавление уже существующего материала
	async function addExistingMaterial(material: MaterialsResponse) {
		const attachedFile: AttachedFile = {
			name: material.title,
			isUploading: false,
			materialId: material.id,
			previewUrl:
				material.file && /\.(jpg|jpeg|png|gif|webp)$/i.test(material.file)
					? pb!.files.getURL(material, material.file)
					: null
		};

		attachedFiles = [...attachedFiles, attachedFile];

		if (quizTemplateId) {
			try {
				const quiz = await pb!.collection('quizes').getOne(quizTemplateId);
				const updatedMaterials = [...(quiz.materials || []), material.id];
				await pb!.collection('quizes').update(quizTemplateId, { materials: updatedMaterials });
			} catch (error) {
				console.error('Failed to attach material to quiz:', error);
			}
		}
	}

	async function removeFile(index: number, attachedFiles: AttachedFile[]) {
		const fileToRemove = attachedFiles[index];

		if (fileToRemove.previewUrl) {
			URL.revokeObjectURL(fileToRemove.previewUrl);
		}

		if (quizTemplateId) {
			try {
				const quiz = await pb!.collection('quizes').getOne(quizTemplateId);
				const updatedMaterials = (quiz.materials || []).filter(
					(id: string) => id !== fileToRemove.materialId
				);
				await pb!.collection('quizes').update(quizTemplateId, { materials: updatedMaterials });
			} catch (error) {
				console.error('Failed to detach material from quiz:', error);
			}
		}

		if (fileToRemove.materialId) {
			try {
				const material = await pb!.collection('materials').getOne(fileToRemove.materialId);
				if ((material as any).status !== 'used') {
					await pb!.collection('materials').delete(fileToRemove.materialId);
				}
			} catch (error) {
				console.error('Failed to delete material:', error);
			}
		}

		attachedFiles.splice(index, 1);
		attachedFiles = attachedFiles;
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
			warningTextInput = true;
		} else {
			warningTextInput = false;
		}
	}

	function getFileIcon(filename: string): string {
		const extension = filename.split('.').pop()?.toLowerCase();

		const iconMap: Record<string, string> = {
			pdf: 'pdf',
			doc: 'doc',
			docx: 'doc',
			xls: 'xls',
			xlsx: 'xls',
			ppt: 'ppt',
			pptx: 'ppt',
			txt: 'txt',
			js: 'js',
			ts: 'js',
			html: 'html',
			css: 'css',
			json: 'json',
			xml: 'xml',
			svg: 'svg'
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
</script>

<div
	class={[
		'mx-auto flex w-full max-w-3xl flex-col gap-2.5 rounded-lg p-2 font-sans transition-colors duration-200',
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
		class="relative flex items-center rounded-3xl border border-base-300 bg-base-300 px-4 py-4 transition-colors duration-200 focus-within:border-base-content/40"
	>
		<button
			bind:this={buttonElement}
			onclick={() => (isMaterialsListOpen = !isMaterialsListOpen)}
			class="mr-2 flex cursor-pointer items-center border-none bg-transparent p-0 text-base-content/60 hover:text-base-content"
			aria-label="Attach files"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="24"
				height="24"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
				class="lucide lucide-paperclip"
				><path
					d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.59a2 2 0 0 1-2.83-2.83l8.49-8.48"
				/></svg
			>
		</button>
		{#if isMaterialsListOpen}
			<div
				bind:this={menuElement}
				class="absolute top-5 left-0 z-10 max-h-screen w-75 rounded-lg border border-base-300 bg-base-100 shadow-lg"
			>
				<div class="p-2">
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
				<div class="border-t border-base-300 p-2">
					<div class="mb-2 text-center text-lg font-medium text-base-content/70">
						Previous Materials
					</div>
					<div class="relative">
						<input
							bind:value={searchQuery}
							placeholder="Search materials..."
							class="w-full rounded border border-base-300 py-1 pr-2 pl-8 text-sm focus:border-primary focus:outline-none"
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
					<div class="mt-2 max-h-67 overflow-y-auto">
						{#each materialsStore.materials.filter((m) => m.title
								.toLowerCase()
								.includes(searchQuery.toLowerCase())) as material}
							<button
								class="w-full cursor-pointer p-2 text-left transition-colors duration-200 hover:bg-primary"
								onclick={() => {
									addExistingMaterial(material);
									isMaterialsListOpen = false;
								}}
							>
								{truncateFileName(material.title, 34)}
							</button>
						{/each}
					</div>
				</div>
			</div>
		{/if}
		<textarea
			placeholder="Write a prompt for your quiz and attach relevant material"
			bind:value={inputText}
			class="max-h-[7.5rem] min-h-[1.5rem] flex-grow resize-none overflow-y-auto border-none bg-transparent py-1 pl-4 text-lg leading-6 outline-none focus:shadow-none focus:ring-0 focus:outline-none"
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
	{#if warningTextInput}
		<div class="text-md mt-2 text-red-500">Maximum input length is 100.000 symbols.</div>
	{/if}
	{#if attachedFiles.length > 0}
		<div class="grid grid-cols-5 gap-4 px-3">
			{#each attachedFiles as attachedFile, index}
				<div class="group relative aspect-square w-full overflow-hidden rounded-lg bg-base-300">
					{#if attachedFile.previewUrl}
						<img
							src={attachedFile.previewUrl}
							alt={attachedFile.name}
							class="h-full w-full object-cover"
						/>
					{:else}
						<div
							class="flex h-full w-full flex-col items-center p-2 text-center text-base-content/60"
						>
							<img
								src="/file-format-icons/{getFileIcon(attachedFile.name)}.svg"
								alt="File icon"
								class="mb-1 h-10 w-10"
							/>
							<span
								class="line-clamp-3 flex h-24 items-center text-[14px] leading-tight break-words break-all"
								title={attachedFile.name}>{truncateFileName(attachedFile.name)}</span
							>
						</div>
					{/if}

					<!-- Индикатор загрузки -->
					{#if attachedFile.isUploading}
						<div class="absolute inset-0 flex items-center justify-center bg-base-content/50">
							<div
								class="h-8 w-8 animate-spin rounded-full border-4 border-base-100 border-t-transparent"
							></div>
						</div>
					{/if}

					<button
						onclick={() => removeFile(index, attachedFiles)}
						class="absolute top-1 right-1 flex h-5 w-5 cursor-pointer items-center justify-center rounded-full border-none bg-base-content/50 text-sm leading-none text-base-100 opacity-0 transition-opacity group-hover:opacity-100"
						aria-label="Remove file">&times;</button
					>
				</div>
			{/each}
		</div>
	{/if}
</div>
