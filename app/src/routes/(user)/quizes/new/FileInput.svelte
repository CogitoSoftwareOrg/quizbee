<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { computeApiUrl } from '$lib/api/compute-url';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import type { AttachedFile } from '$lib/types/attached-file';
	import { pb } from '$lib/pb';
	import type { MaterialsResponse } from '$lib/pb/pocketbase-types';
	function generateId(): string {
		const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
		let result = '';
		for (let i = 0; i < 15; i++) {
			result += chars.charAt(Math.floor(Math.random() * chars.length));
		}
		return result;
	}

	function processFiles(files: File[]) {
		for (const file of files) {
			const attachedFile: AttachedFile = {
				file,
				previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : null,
				name: file.name,
				isUploading: true,
				uploadError: undefined,
				materialId: generateId()
			};

			attachedFiles = [...attachedFiles, attachedFile];
			uploadFileAsync(attachedFile);
		}
	}

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
	let previousAttachedFiles = attachedFiles;
	let isMaterialsListOpen = $state(false);
	let searchQuery = $state('');

	let buttonElement = $state<HTMLButtonElement>();
	let menuElement = $state<HTMLDivElement>();

	// Реактивно отслеживаем материалы в store и обновляем статус загрузки
	$effect(() => {
		const materials = materialsStore.materials;

		// Проходим по всем прикрепленным файлам и проверяем их статус
		attachedFiles.forEach((attachedFile) => {
			if (attachedFile.isUploading && attachedFile.materialId) {
				// Ищем материал в store по ID
				const foundMaterial = materials.find((material) => material.id === attachedFile.materialId);

				if (foundMaterial) {
					// Материал найден в store - обновляем статус
					attachedFile.isUploading = false;
					console.log(`Material ${attachedFile.name} found in store, setting isUploading to false`);
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

	// Асинхронная загрузка файла без блокировки UI
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

			// Проверяем, что получили material.id
			if (!material.id) {
				throw new Error('Material ID not received from API');
			}

			// Обновляем materialId после успешной загрузки
			// isUploading будет автоматически обновлен через реактивность когда материал появится в store
			attachedFile.materialId = material.id;

			// Добавляем информацию о токенах если есть
			if (material.tokens) {
				attachedFile.tokens = material.tokens;
			}

			console.log(`File ${attachedFile.name} uploaded successfully with ID: ${material.id}`);

			try {
				// Добавляем проверку прямо здесь
				if (!quizTemplateId) {
					console.error('quizTemplateId is missing, cannot attach material.');
					// Можно просто прервать выполнение или уведомить пользователя
					return;
				}

				const quiz = await pb!.collection('quizes').getOne(quizTemplateId);
				const updatedMaterials = [...(quiz.materials || []), material.id];
				await pb!.collection('quizes').update(quizTemplateId, { materials: updatedMaterials });
				console.log(`Material ${material.id} attached to quiz ${quizTemplateId}`);
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

	async function addExistingMaterial(material: MaterialsResponse) {
		const attachedFile: AttachedFile = {
			name: material.title,
			isUploading: false,
			materialId: material.id,
			previewUrl:
				material.file && /\.(jpg|jpeg|png|gif|webp)$/i.test(material.file) ? material.file : null
		};

		attachedFiles = [...attachedFiles, attachedFile];

		if (quizTemplateId) {
			try {
				const quiz = await pb!.collection('quizes').getOne(quizTemplateId);
				const updatedMaterials = [...(quiz.materials || []), material.id];
				await pb!.collection('quizes').update(quizTemplateId, { materials: updatedMaterials });
				console.log(`Material ${material.id} attached to quiz ${quizTemplateId}`);
			} catch (error) {
				console.error('Failed to attach material to quiz:', error);
			}
		}
	}
	async function removeFile(index: number, attachedFiles: AttachedFile[]) {
		const fileToRemove = attachedFiles[index];

		// Освобождаем URL превью если есть
		if (fileToRemove.previewUrl) {
			URL.revokeObjectURL(fileToRemove.previewUrl);
		}

		// Открепляем материал от квиза
		if (quizTemplateId) {
			try {
				const quiz = await pb!.collection('quizes').getOne(quizTemplateId);
				const updatedMaterials = (quiz.materials || []).filter(
					(id: string) => id !== fileToRemove.materialId
				);
				await pb!.collection('quizes').update(quizTemplateId, { materials: updatedMaterials });
				console.log(`Material ${fileToRemove.materialId} detached from quiz ${quizTemplateId}`);
			} catch (error) {
				console.error('Failed to detach material from quiz:', error);
			}
		}

		// Удаляем материал с сервера если он не используется
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

		// Удаляем из списка
		attachedFiles.splice(index, 1);
		attachedFiles = attachedFiles;
	}
	async function handlePaste(event: ClipboardEvent) {
		const clipboardData = event.clipboardData;
		if (!clipboardData) return;

		const items = Array.from(clipboardData.items);
		const imageItems = items.filter((item) => item.type.startsWith('image/'));

		if (imageItems.length > 0) {
			event.preventDefault(); // Предотвращаем вставку текста

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
		const maxHeight = 7.5 * 16; // 7.5rem в пикселях (предполагая 16px = 1rem)
		target.style.height = Math.min(scrollHeight, maxHeight) + 'px';
	}

	function getFileIcon(filename: string): string {
		const extension = filename.split('.').pop()?.toLowerCase();

		// Маппинг расширений файлов на иконки
		const iconMap: Record<string, string> = {
			// Документы
			pdf: 'pdf',
			doc: 'doc',
			docx: 'doc',
			xls: 'xls',
			xlsx: 'xls',
			ppt: 'ppt',
			pptx: 'ppt',
			txt: 'txt',

			// Архивы
			zip: 'zip',

			// Код
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

	onMount(() => {
		document.addEventListener('click', handleClickOutside);
	});

	onDestroy(() => {
		document.removeEventListener('click', handleClickOutside);
		// Освобождаем все URL превью
		attachedFiles.forEach((attachedFile) => {
			if (attachedFile.previewUrl) {
				URL.revokeObjectURL(attachedFile.previewUrl);
			}
		});

		// Примечание: Мы НЕ удаляем материалы с сервера при уничтожении компонента,
		// так как они могут быть использованы в других местах приложения
	});
</script>

<div
	class={[
		'mx-auto flex w-full max-w-3xl flex-col gap-2.5 rounded-lg p-2 font-sans transition-colors duration-200',
		isDragging && 'bg-primary/10 border-primary border-2 border-dashed'
	]}
	ondragover={handleDragOver}
	ondragleave={handleDragLeave}
	ondrop={handleDrop}
	role="button"
	tabindex="0"
	aria-label="Drop files here or click to upload"
>
	<div
		class="border-base-300 bg-base-300 focus-within:border-base-content/40 relative flex items-center rounded-3xl border px-4 py-4 transition-colors duration-200"
	>
		<button
			bind:this={buttonElement}
			onclick={() => (isMaterialsListOpen = !isMaterialsListOpen)}
			class="text-base-content/60 hover:text-base-content mr-2 flex cursor-pointer items-center border-none bg-transparent p-0"
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
				class="bg-base-100 border-base-300 w-75 absolute left-8 top-10 z-10 max-h-screen rounded-lg border shadow-lg"
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
							class="text-base-content/60 lucide lucide-search absolute left-2 top-1/2 -translate-y-1/2 transform"
							><circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" /></svg
						>
					</div>
					<div class="max-h-67 mt-2 overflow-y-auto">
						{#each materialsStore.materials.filter((m) => m.title
								.toLowerCase()
								.includes(searchQuery.toLowerCase())) as material}
							<button
								class="hover:bg-primary w-full cursor-pointer p-2 text-left transition-colors duration-200"
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
			class="max-h-[7.5rem] min-h-[1.5rem] flex-grow resize-none overflow-y-auto border-none bg-transparent py-1 pl-4 text-lg leading-6 outline-none focus:shadow-none focus:outline-none focus:ring-0"
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
	{#if attachedFiles.length > 0}
		<div class="grid grid-cols-5 gap-4 px-3">
			{#each attachedFiles as attachedFile, index}
				<div class="bg-base-300 group relative aspect-square w-full overflow-hidden rounded-lg">
					{#if attachedFile.previewUrl}
						<img
							src={attachedFile.previewUrl}
							alt={attachedFile.name}
							class="h-full w-full object-cover"
						/>
					{:else}
						<div
							class="text-base-content/60 flex h-full w-full flex-col items-center p-2 text-center"
						>
							<img
								src="/file-format-icons/{getFileIcon(attachedFile.name)}.svg"
								alt="File icon"
								class="mb-1 h-10 w-10"
							/>
							<span
								class="line-clamp-3 flex h-24 items-center break-words break-all text-[14px] leading-tight"
								title={attachedFile.name}>{truncateFileName(attachedFile.name)}</span
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
						onclick={() => removeFile(index, attachedFiles)}
						class="bg-base-content/50 text-base-100 absolute right-1 top-1 flex h-5 w-5 cursor-pointer items-center justify-center rounded-full border-none text-sm leading-none opacity-0 transition-opacity group-hover:opacity-100"
						aria-label="Remove file">&times;</button
					>
				</div>
			{/each}
		</div>
	{/if}
</div>
