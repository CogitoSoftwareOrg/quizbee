<script lang="ts">
  import type { QuizesResponse } from "@quizbee/pb-types";

  export let quiz: QuizesResponse;
  export let href: string;

  const difficulty = quiz.difficulty ?? "beginner";
  const itemsCount = quiz.itemsLimit ?? 0;
</script>

<a
  {href}
  class="group rounded-2xl bg-card overflow-hidden hover:shadow-lg transition-shadow border border-base-300 block text-left"
>
  <div class="p-5">
    <div class="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
      <span class="capitalize font-medium text-primary">
        {difficulty}
      </span>
      {#if itemsCount > 0}
        <span>·</span>
        <span>{itemsCount} questions</span>
      {/if}
      {#if quiz.generation}
        <span>·</span>
        <span class="capitalize">v{quiz.generation}</span>
      {/if}
      {#if quiz.archived}
        <span class="badge badge-xs badge-warning">Archived</span>
      {/if}
    </div>

    <h2
      class="text-lg font-bold leading-snug group-hover:text-primary transition-colors line-clamp-2 mb-2"
    >
      {quiz.title ?? quiz.slug}
    </h2>

    {#if quiz.summary}
      <p class="text-sm text-muted-foreground line-clamp-2 mb-3">
        {quiz.summary}
      </p>
    {/if}

    {#if Array.isArray(quiz.tags) && quiz.tags.length > 0}
      <div class="flex flex-wrap gap-2">
        {#each quiz.tags.slice(0, 3) as tag}
          <span
            class="text-[11px] text-muted-foreground bg-muted px-2 py-1 rounded-full"
          >
            #{tag}
          </span>
        {/each}
      </div>
    {/if}
  </div>
</a>
