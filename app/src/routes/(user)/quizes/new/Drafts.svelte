<script lang="ts">
    import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
    import { materialsStore } from '$lib/apps/materials/materials.svelte';
    import type { AttachedFile } from '$lib/types/attached-file';
    import {pb} from '$lib/pb';
    import {createAttachedFileFromMaterial} from '../new/createAttachedFileFromMaterial';
    import { generateId } from '$lib/utils/generate-id';
    import { untrack } from 'svelte';
    import { onMount  } from 'svelte';
	import { is } from 'zod/locales';
	import { set } from 'zod';

    
    interface Props {
        quizTemplateId: string;
        
        title: string;
        inputText: string;  
        attachedFiles: AttachedFile[];
        selectedDifficulty: string;
        questionCount: number;
        isDraft: boolean;
    
    }

    async function createDraftFromCurrent() {
		const currentQuiz = quizesStore.quizes.find(q => q.id === quizTemplateId);
		if (!currentQuiz) return;

		const newId = generateId();
		const formData = new FormData();
		formData.append('status', 'draft');
		formData.append('query', inputText);
		formData.append('materials', JSON.stringify(currentQuiz.materials || []));
		formData.append('difficulty', selectedDifficulty);
		formData.append('itemsLimit', questionCount.toString());
		formData.append('author', pb!.authStore.model?.id || '');
		formData.append('title', `Draft from ${currentQuiz.title || 'Quiz'}`);
		formData.append('id', newId);

        

		pb!.collection('quizes').create(formData);
		quizTemplateId = newId;
	}

	

    let { title = $bindable(), quizTemplateId = $bindable(), inputText = $bindable(), attachedFiles = $bindable(), selectedDifficulty = $bindable(), questionCount = $bindable(), isDraft = $bindable() }: Props = $props();

    // drafts from store
    const drafts = $derived(quizesStore.quizes.filter((q: any) => q.status === 'draft'));

    // Автоматическое обновление сложности в PB
    let isAddingDraft = false;
    $effect(() => {
            
            if (!untrack(() => isAddingDraft) && untrack(() => isDraft) && untrack(() => quizTemplateId) && selectedDifficulty) {
                    
               
                    pb!.collection('quizes').update(untrack(() => quizTemplateId), { difficulty: selectedDifficulty })
                
            }
        }
    );

    // Автоматическое обновление количества вопросов в PB
    $effect(() => {
        if (!untrack(() => isAddingDraft) && untrack(() => isDraft) && untrack(() => quizTemplateId) && questionCount) {
            pb!.collection('quizes').update(untrack(() => quizTemplateId), { itemsLimit: questionCount });
        }
    });

    
    let debounceTimeout: ReturnType<typeof setTimeout> | undefined;

    $effect(() => {
        if (!untrack(() => isAddingDraft) && untrack(() => isDraft) && untrack(() => quizTemplateId) && inputText) {
            if (debounceTimeout) {
                clearTimeout(debounceTimeout);
            }
            debounceTimeout = setTimeout(() => {
                pb!.collection('quizes').update(untrack(() => quizTemplateId), { query: inputText });
            }, 750);
        }
    });

  
    $effect(() => {
        
        [inputText, attachedFiles, selectedDifficulty, questionCount];
        const newId = generateId();
        if (!isDraft) {
           
            createDraftFromCurrent();
          
            setTimeout(() => {
                isDraft = true;
            }, 0);
        }
    });

    
    // if there are no drafts of this user -> create one. otherwise take the first draft he has
    onMount(() => {
        
        if (quizesStore.quizes.filter(q => q.status === 'draft').length==0) {

            addDraft();

        } 
        else {
            quizTemplateId = drafts[0].id;
            inputText = drafts[0].query;
            attachedFiles = drafts[0].materials.map((materialId: string) => {
                    return createAttachedFileFromMaterial(materialId, drafts[0].status);
            });
            selectedDifficulty = drafts[0].difficulty;
            questionCount = drafts[0].itemsLimit;
        }
    });

    async function handleDraftClick(draft: any) {
       quizTemplateId = draft.id;
       inputText = draft.query;
       attachedFiles = draft.materials.map((materialId: string) => {
           return createAttachedFileFromMaterial(materialId, draft.status);
       });
       selectedDifficulty = draft.difficulty;
       questionCount = draft.itemsLimit;
    }

    async function handleDelete(draft: any) {
        if (confirm('Are you sure you want to delete this draft?')) {
            await pb!.collection('quizes').delete(draft.id);
            quizesStore.quizes = quizesStore.quizes.filter(q => q.id !== draft.id);
            if (quizTemplateId === draft.id) {
                quizTemplateId = '';
                inputText = '';
                attachedFiles = [];
                selectedDifficulty = 'intermediate';
                questionCount = 10;
            }
        }
    }

    async function addDraft() {
        isAddingDraft = true;

        
        const newId = generateId();
        const formData = new FormData();
        formData.append('status', 'draft');
        formData.append('query', '');
        formData.append('attachedFiles', JSON.stringify([]));
        formData.append('difficulty', 'intermediate');
        formData.append('questionCount', '10');
        formData.append('author', pb!.authStore.model?.id || '');
        formData.append('title', `Draft ${drafts.length + 1}`);
        formData.append('id', newId);

        pb!.collection('quizes').create(formData);
       
        quizTemplateId = newId;
        inputText = '';
        attachedFiles = [];
        selectedDifficulty = 'intermediate';
        questionCount = 10;
        
        setTimeout(() => {
            isAddingDraft = false;
        }, 0);
      

     

        
    }
</script>

<div class="mb-6">
    <h2 class="mb-3 text-center text-lg font-semibold">Drafts</h2>
    <div class="flex justify-center mb-3">
        <button class="btn btn-primary btn-sm" onclick={addDraft}>Add Draft</button>
    </div>

    {#if drafts.length === 0}
        <div class="text-center">
            <p class="text-sm">No drafts yet</p>
            <p class="mt-1 text-xs">Start drafting your quiz and it will appear here.</p>
        </div>
    {:else}
        <div class="space-y-3">
            {#each drafts as draft}
                <div
                    class="relative border-base-200 cursor-pointer rounded-lg border p-3 shadow-sm transition-shadow hover:shadow-md"
                    class:bg-yellow-100={draft.id === quizTemplateId}
                    onclick={() => handleDraftClick(draft)}
                    onkeydown={(e) => e.key === 'Enter' && handleDraftClick(draft)}
                    role="button"
                    tabindex="0"
                >
                    <div class="mb-1 truncate font-medium" title={draft.title || `Draft ${draft.id}`}>
                        {draft.title || `Draft ${draft.id}`}
                    </div>
                    <div class="text-xs text-muted">
                        {#if draft.updated}
                            Last updated: {new Date(draft.updated).toLocaleString()}
                        {:else}
                            Created: {new Date(draft.created).toLocaleString()}
                        {/if}
                    </div>
                    {#if drafts.length > 1}
                        <button 
                            class="absolute top-2 right-2 text-red-500 hover:text-red-700 text-lg" 
                            onclick={(e) => { e.stopPropagation(); handleDelete(draft); }}
                            title="Delete draft"
                        >
                            &times;
                        </button>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}
</div>
