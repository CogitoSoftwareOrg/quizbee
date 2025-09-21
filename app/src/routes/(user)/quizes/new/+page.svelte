<script lang="ts">
    let attachedFiles: FileList | null = null;

    function handleSubmit() {
        console.log('Файлы:', attachedFiles);
    }

    function handleFileChange(event: Event) {
        const target = event.target as HTMLInputElement;
        attachedFiles = target.files;
    }
</script>

<svelte:head>
    <title>New Quiz</title>
</svelte:head>

<main class="p-8 max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold mb-8">Новый квиз</h1>
    
    <div class="space-y-6">
        <!-- Форма создания квиза -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h2 class="card-title">Детали квиза</h2>
                
                <!-- Название квиза -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Название квиза</span>
                    </label>
                    <input type="text" class="input input-bordered" placeholder="Введите название квиза" />
                </div>

                <!-- Описание квиза -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Описание</span>
                    </label>
                    <textarea class="textarea textarea-bordered" placeholder="Введите описание квиза"></textarea>
                </div>

                <!-- Дополнительные материалы -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Дополнительные материалы</span>
                    </label>
                    <input 
                        type="file" 
                        class="file-input file-input-bordered w-full" 
                        multiple
                        accept="image/*,.pdf,.doc,.docx"
                        on:change={handleFileChange}
                    />
                </div>

                <div class="card-actions justify-end mt-6">
                    <button class="btn btn-primary" on:click={handleSubmit}>
                        Создать квиз
                    </button>
                </div>
            </div>
        </div>
    </div>
</main>

<style>
    /* Убираем старые стили, используем Tailwind/DaisyUI */
</style>