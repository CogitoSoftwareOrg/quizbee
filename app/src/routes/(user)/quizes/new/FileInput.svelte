<script lang="ts">
	import { onDestroy } from 'svelte';
	import { computeApiUrl } from '$lib/api/compute-url';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import type { AttachedFile } from '$lib/types/attached-file';
	import { pb } from '$lib/pb';
	
	function generateId(): string {
		const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
		let result = '';
		for (let i = 0; i < 15; i++) {
			result += chars.charAt(Math.floor(Math.random() * chars.length));
		}
		return result;
	}

	interface Props {
		inputText?: string;
		attachedFiles?: AttachedFile[];
	}


	
	let { inputText = $bindable(''), attachedFiles = $bindable([]) }: Props = $props();

	let inputElement: HTMLInputElement;
	let isDragging = $state(false);

	// Реактивно отслеживаем материалы в store и обновляем статус загрузки
	$effect(() => {
		const materials = materialsStore.materials;
		
		// Проходим по всем прикрепленным файлам и проверяем их статус
		attachedFiles.forEach((attachedFile) => {
			if (attachedFile.isUploading && attachedFile.materialId) {
				// Ищем материал в store по ID
				const foundMaterial = materials.find(material => material.id === attachedFile.materialId);
				
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
			const newFiles = Array.from(target.files);
			
			// Добавляем все файлы в UI сразу и запускаем загрузку асинхронно
			for (const file of newFiles) {
				const attachedFile: AttachedFile = {
					file,
					previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : null,
					name: file.name,
					isUploading: true,
					uploadError: undefined,
					materialId: generateId(),
				};

				// Добавляем файл в UI сразу (с индикатором загрузки)
				attachedFiles = [...attachedFiles, attachedFile];

				// Запускаем загрузку асинхронно без ожидания
				uploadFileAsync(attachedFile);
			}
		}
	}

	// Асинхронная загрузка файла без блокировки UI
	async function uploadFileAsync(attachedFile: AttachedFile) {
		try {
			const formData = new FormData();
			formData.append('file', attachedFile.file!);
			formData.append('title', attachedFile.name);
			formData.append('material_id', attachedFile.materialId!);

			const response = await fetch(`${computeApiUrl()}/materials/upload`, {
				method: 'POST',
				body: formData,
				credentials: 'include',
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

	

	async function removeFile(index: number) {
		const fileToRemove = attachedFiles[index];
		
		// Освобождаем URL превью если есть
		if (fileToRemove.previewUrl) {
			URL.revokeObjectURL(fileToRemove.previewUrl);
		}
		
		// Удаляем материал с сервера если он был загружен
		if (fileToRemove.materialId) {
			try {
				
				pb!.collection('materials').delete(fileToRemove.materialId);

			} catch (error) {
				console.error('Failed to delete material from server:', error);
				// Не блокируем удаление из UI даже если не удалось удалить с сервера
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
		const imageItems = items.filter(item => item.type.startsWith('image/'));

		if (imageItems.length > 0) {
			event.preventDefault(); // Предотвращаем вставку текста

			const files = imageItems.map(item => item.getAsFile()).filter(file => file !== null) as File[];
			
			// Добавляем все файлы в UI сразу и запускаем загрузку асинхронно
			for (const file of files) {
				const attachedFile: AttachedFile = {
					file,
					previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : null,
					name: file.name,
					isUploading: true,
					uploadError: undefined,
					materialId: generateId(),
				};

				// Добавляем файл в UI сразу (с индикатором загрузки)
				attachedFiles = [...attachedFiles, attachedFile];

				// Запускаем загрузку асинхронно без ожидания
				uploadFileAsync(attachedFile);
			}
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
			const newFiles = Array.from(files);
			
			// Добавляем все файлы в UI сразу и запускаем загрузку асинхронно
			for (const file of newFiles) {
				const attachedFile: AttachedFile = {
					file,
					previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : null,
					name: file.name,
					isUploading: true,
					uploadError: undefined,
					materialId: generateId(),
				};

				// Добавляем файл в UI сразу (с индикатором загрузки)
				attachedFiles = [...attachedFiles, attachedFile];

				// Запускаем загрузку асинхронно без ожидания
				uploadFileAsync(attachedFile);
			}
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
			'pdf': 'pdf',
			'doc': 'doc',
			'docx': 'doc',
			'xls': 'xls',
			'xlsx': 'xls',
			'ppt': 'ppt',
			'pptx': 'ppt',
			'txt': 'txt',
			
			
			// Архивы
			'zip': 'zip',
			

			
			// Код
			'js': 'js',
			'ts': 'js',
			'html': 'html',
			'css': 'css',
			'json': 'json',
			'xml': 'xml',
			'svg': 'svg',
			
			
		};
		
		return iconMap[extension || ''] || 'unknown';
	}

	function truncateFileName(filename: string, maxLength: number = 50): string {
		if (filename.length <= maxLength) {
			return filename;
		}
		return filename.substring(0, maxLength - 3) + '...';
	}

	onDestroy(() => {
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
		"flex flex-col gap-2.5 w-full max-w-3xl mx-auto font-sans transition-colors duration-200 rounded-lg p-2",
		isDragging && "bg-primary/10 border-2 border-dashed border-primary"
	]}
	ondragover={handleDragOver}
	ondragleave={handleDragLeave}
	ondrop={handleDrop}
	role="button"
	tabindex="0"
	aria-label="Drop files here or click to upload"
>
	<div class="flex items-center border border-base-300 rounded-3xl px-4 py-4 bg-base-300 transition-colors duration-200 focus-within:border-base-content/40">
		<button onclick={openFileDialog} class="bg-transparent border-none cursor-pointer p-0 mr-2 flex items-center text-base-content/60 hover:text-base-content" aria-label="Attach files">
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
		<textarea 
			placeholder="Write a prompt for your quiz and attach relevant material" 
			bind:value={inputText}
			class="flex-grow border-none outline-none bg-transparent text-lg py-1 pl-4 focus:outline-none focus:ring-0 focus:shadow-none resize-none overflow-y-auto min-h-[1.5rem] max-h-[7.5rem] leading-6"
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
				<div class="group relative w-full aspect-square rounded-lg overflow-hidden bg-base-300">
					{#if attachedFile.previewUrl}
						<img src={attachedFile.previewUrl} alt={attachedFile.name} class="w-full h-full object-cover" />
					{:else}
						<div class="flex flex-col items-center w-full h-full p-2 text-center text-base-content/60">
							<img src="/file-format-icons/{getFileIcon(attachedFile.name)}.svg" alt="File icon" class="w-10 h-10 mb-1" />
							<span class="text-[14px] break-words break-all line-clamp-3 leading-tight h-24 flex items-center" title={attachedFile.name}>{truncateFileName(attachedFile.name)}</span>
						</div>
					{/if}
					
					<!-- Индикатор загрузки -->
					{#if attachedFile.isUploading}
						<div class="absolute inset-0 bg-base-content/50 flex items-center justify-center">
							<div class="w-8 h-8 border-4 border-base-100 border-t-transparent rounded-full animate-spin"></div>
						</div>
					{/if}
					
					<button onclick={() => removeFile(index)} class="absolute top-1 right-1 bg-base-content/50 text-base-100 border-none rounded-full w-5 h-5 flex items-center justify-center cursor-pointer text-sm leading-none opacity-0 transition-opacity group-hover:opacity-100" aria-label="Remove file"
						>&times;</button
					>
				</div>
			{/each}
		</div>
	{/if}
</div>


