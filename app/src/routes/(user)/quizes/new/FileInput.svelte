<script lang="ts">
	import { onDestroy, untrack } from 'svelte';

	type FilePreview = {
		file: File;
		previewUrl: string | null;
	};

	interface Props {
		inputText?: string;
		attachedFiles?: File[];
	}

	let { inputText = $bindable(''), attachedFiles = $bindable([]) }: Props = $props();

	let filePreviews = $state<FilePreview[]>([]);
	let inputElement: HTMLInputElement;
	let isDragging = $state(false);

	
	// Обновляем attachedFiles когда меняется filePreviews
	$effect(() => {
		if (filePreviews.length > 0) {
			const files = filePreviews.map(fp => fp.file);
			const fileList = new DataTransfer();
			files.forEach(file => fileList.items.add(file));
			attachedFiles = Array.from(fileList.files);
		} else {
			untrack(() => {
				attachedFiles = [];
			});
		}
	});

	function handleGlobalFiles(files: File[]) {
		const newFiles = Array.from(files);
		const newFilePreviews = newFiles.map((file) => ({
			file,
			previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
		}));
		filePreviews = [...filePreviews, ...newFilePreviews];
	}

	function openFileDialog() {
		inputElement.click();
	}

	function handleFileChange(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files) {
			const newFiles = Array.from(target.files);
			const newFilePreviews = newFiles.map((file) => ({
				file,
				previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
			}));
			filePreviews = [...filePreviews, ...newFilePreviews];
		}
	}

	function removeFile(index: number) {
		const fileToRemove = filePreviews[index];
		if (fileToRemove.previewUrl) {
			URL.revokeObjectURL(fileToRemove.previewUrl);
		}
		filePreviews.splice(index, 1);
		filePreviews = filePreviews;
	}

	function handlePaste(event: ClipboardEvent) {
		const clipboardData = event.clipboardData;
		if (!clipboardData) return;

		const items = Array.from(clipboardData.items);
		const imageItems = items.filter(item => item.type.startsWith('image/'));

		if (imageItems.length > 0) {
			event.preventDefault(); // Предотвращаем вставку текста

			imageItems.forEach(item => {
				const file = item.getAsFile();
				if (file) {
					const newFilePreview = {
						file,
						previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
					};
					filePreviews = [...filePreviews, newFilePreview];
				}
			});
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

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		isDragging = false;

		const files = event.dataTransfer?.files;
		if (files) {
			const newFiles = Array.from(files);
			const newFilePreviews = newFiles.map((file) => ({
				file,
				previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
			}));
			filePreviews = [...filePreviews, ...newFilePreviews];
		}
	}

	function handleKeyDown(event: KeyboardEvent) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			openFileDialog();
		}
	}

	function getFileExtension(filename: string): string {
		const extension = filename.split('.').pop()?.toUpperCase();
		return extension || 'FILE';
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

	onDestroy(() => {
		filePreviews.forEach((fp) => {
			if (fp.previewUrl) {
				URL.revokeObjectURL(fp.previewUrl);
			}
		});
	});
</script>

<div 
	class="file-input-container"
	class:dragging={isDragging}
	ondragover={handleDragOver}
	ondragleave={handleDragLeave}
	ondrop={handleDrop}
	onkeydown={handleKeyDown}
	role="button"
	tabindex="0"
	aria-label="Drop files here or click to upload"
>
	<div class="input-wrapper">
		<button onclick={openFileDialog} class="attach-btn" aria-label="Attach files">
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
		<input 
			type="text" 
			placeholder="Write a prompt for your quiz and attach relevant material" 
			bind:value={inputText}
			class="text-input"
			onpaste={handlePaste}
		/>
		<input
			type="file"
			bind:this={inputElement}
			onchange={handleFileChange}
			multiple
			style="display: none;"
		/>
	</div>
	{#if filePreviews.length > 0}
		<div class="files-preview">
			{#each filePreviews as { file, previewUrl }, index}
				<div class="file-item">
					{#if previewUrl}
						<img src={previewUrl} alt={file.name} class="image-preview" />
					{:else}
						<div class="file-placeholder">
							
							<img src="/file-format-icons/{getFileIcon(file.name)}.svg" alt="File icon" class="file-icon" />
							<span class="file-name">{file.name}</span>
						</div>
					{/if}
					<button onclick={() => removeFile(index)} class="remove-btn" aria-label="Remove file"
						>&times;</button
					>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.file-input-container {
		display: flex;
		flex-direction: column;
		gap: 10px;
		width: 100%;
		max-width: 800px;
		margin: 0 auto;
		font-family: sans-serif;
		transition: background-color 0.2s ease;
		border-radius: 8px;
		padding: 8px;
	}

	.file-input-container.dragging {
		background-color: #e8f0fe;
		border: 2px dashed #4285f4;
	}

	.input-wrapper {
		display: flex;
		align-items: center;
		border: 1px solid #ccc;
		border-radius: 24px;
		padding: 16px 16px;
		background-color: #f8f9fa;
		transition: border-color 0.2s ease;
	}

	.input-wrapper:focus-within {
		border-color: #dadce0;
		outline: none;
	}

	.text-input {
		flex-grow: 1;
		border: none;
		outline: none;
		background: none;
		font-size: 18px;
		padding: 4px 0 4px 16px;
	}

	.text-input:focus {
		outline: none;
		box-shadow: none;
	}

	.attach-btn {
		background: none;
		border: none;
		cursor: pointer;
		padding: 0;
		margin-right: 8px;
		display: flex;
		align-items: center;
		color: #5f6368;
	}

	.attach-btn:hover {
		color: #202124;
	}

	.files-preview {
		display: grid;
		grid-template-columns: repeat(auto-fit, 140px);
		gap: 16px;
		padding: 0 12px;
		justify-content: start;
	}

	.file-item {
		position: relative;
		width: 150px;
		height: 150px;
		border-radius: 8px;
		overflow: hidden;
		background-color: #e8eaed;
	}

	.image-preview {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.file-placeholder {
		display: flex;
		flex-direction: column;
		align-items: center;
		width: 100%;
		height: 100%;
		padding: 8px;
		text-align: center;
		color: #5f6368;
	}

	.file-name {
		font-size: 13px;
		word-break: break-all;
		display: -webkit-box;
		-webkit-line-clamp: 3;
		line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
		text-overflow: ellipsis;
		margin-top: auto;
		flex-grow: 1;
		display: flex;
		align-items: flex-end;
	}

	.file-icon {
		width: 48px;
		height: 48px;
		margin: 8px 0;
	}

	.remove-btn {
		position: absolute;
		top: 4px;
		right: 4px;
		background: rgba(0, 0, 0, 0.5);
		color: white;
		border: none;
		border-radius: 50%;
		width: 20px;
		height: 20px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		font-size: 14px;
		line-height: 1;
		opacity: 0;
		transition: opacity 0.2s;
	}

	.file-item:hover .remove-btn {
		opacity: 1;
	}
</style>
