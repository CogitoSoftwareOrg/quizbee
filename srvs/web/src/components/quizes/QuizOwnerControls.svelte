<script lang="ts">
  import { pb } from "@/lib/pb";
  import { Pencil, Archive, Save, X, Loader2 } from "lucide-svelte";
  import { onMount } from "svelte";

  export let quizId: string;
  export let authorId: string;
  export let initialTitle: string;
  export let isArchived: boolean = false;

  let isOwner = false;
  let isEditing = false;
  let title = initialTitle;
  let isLoading = false;

  onMount(() => {
    isOwner = pb.authStore.model?.id === authorId;
  });

  async function saveTitle() {
    if (!title.trim()) return;

    isLoading = true;
    try {
      await pb.collection("quizes").update(quizId, {
        title: title,
      });
      initialTitle = title;
      isEditing = false;
    } catch (err) {
      console.error("Failed to update title", err);
      alert("Failed to update title");
    } finally {
      isLoading = false;
    }
  }

  async function archiveQuiz() {
    if (
      !confirm(
        "Are you sure you want to archive this quiz? It will become private."
      )
    )
      return;

    isLoading = true;
    try {
      await pb.collection("quizes").update(quizId, {
        archived: true,
        visibility: "private",
      });
      isArchived = true;
      window.location.reload();
    } catch (err) {
      console.error("Failed to archive quiz", err);
      alert("Failed to archive quiz");
    } finally {
      isLoading = false;
    }
  }

  function cancelEdit() {
    title = initialTitle;
    isEditing = false;
  }
</script>

{#if isOwner}
  <div class="flex items-center gap-2 mb-4">
    {#if isEditing}
      <div class="flex items-center gap-2 w-full max-w-md">
        <input
          type="text"
          bind:value={title}
          class="input input-bordered input-sm w-full"
          disabled={isLoading}
        />
        <button
          class="btn btn-square btn-sm btn-primary"
          on:click={saveTitle}
          disabled={isLoading}
        >
          {#if isLoading}
            <Loader2 class="w-4 h-4 animate-spin" />
          {:else}
            <Save class="w-4 h-4" />
          {/if}
        </button>
        <button
          class="btn btn-square btn-sm btn-ghost"
          on:click={cancelEdit}
          disabled={isLoading}
        >
          <X class="w-4 h-4" />
        </button>
      </div>
    {:else}
      <button
        class="btn btn-ghost btn-sm gap-2 text-muted-foreground hover:text-foreground"
        on:click={() => (isEditing = true)}
      >
        <Pencil class="w-4 h-4" />
        Edit Title
      </button>

      {#if !isArchived}
        <button
          class="btn btn-ghost btn-sm gap-2 text-error hover:bg-error/10"
          on:click={archiveQuiz}
          disabled={isLoading}
        >
          <Archive class="w-4 h-4" />
          Archive
        </button>
      {/if}
    {/if}
  </div>
{/if}
