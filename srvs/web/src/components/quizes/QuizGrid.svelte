<script lang="ts">
  import { pb } from "@/lib/pb";
  import QuizCard from "./QuizCard.svelte";
  import type { QuizesResponse } from "@quizbee/pb-types";
  import { Loader2 } from "lucide-svelte";

  export let initialQuizzes: QuizesResponse[] = [];
  export let category: string;
  export let localePrefix: string = "";

  let showArchived = false;
  let archivedQuizzes: QuizesResponse[] = [];
  let isLoading = false;
  let hasLoadedArchived = false;

  $: displayedQuizzes = showArchived
    ? [...initialQuizzes, ...archivedQuizzes].sort(
        (a, b) => new Date(b.created).getTime() - new Date(a.created).getTime()
      )
    : initialQuizzes;

  async function toggleArchived() {
    showArchived = !showArchived;

    if (showArchived && !hasLoadedArchived) {
      isLoading = true;
      try {
        // Fetch archived quizzes for this category
        // Note: This assumes the user has permission to see their own archived quizzes
        // The rule in PB should allow owners to list their own archived quizzes
        const res = await pb.collection("quizes").getList(1, 50, {
          filter: `category = "${category}" && archived = true`,
          sort: "-created",
        });
        archivedQuizzes = res.items;
        hasLoadedArchived = true;
      } catch (err) {
        console.error("Failed to load archived quizzes", err);
      } finally {
        isLoading = false;
      }
    }
  }

  function getHref(quiz: QuizesResponse) {
    const prefix = localePrefix ? `/${localePrefix}` : "";
    return `${prefix}/quizes/${quiz.category}/${quiz.slug || quiz.id}`;
  }
</script>

<div class="flex justify-end mb-4">
  <label class="label cursor-pointer gap-2">
    <span class="label-text text-muted-foreground">Show Archived</span>
    <input
      type="checkbox"
      class="toggle toggle-sm toggle-primary"
      checked={showArchived}
      on:change={toggleArchived}
      disabled={isLoading}
    />
  </label>
</div>

{#if isLoading}
  <div class="flex justify-center py-8">
    <Loader2 class="w-8 h-8 animate-spin text-primary" />
  </div>
{:else}
  <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
    {#each displayedQuizzes as quiz (quiz.id)}
      <QuizCard {quiz} href={getHref(quiz)} />
    {/each}
  </section>

  {#if displayedQuizzes.length === 0}
    <div class="text-center py-12">
      <p class="text-muted-foreground">No quizes found in this category yet.</p>
    </div>
  {/if}
{/if}
