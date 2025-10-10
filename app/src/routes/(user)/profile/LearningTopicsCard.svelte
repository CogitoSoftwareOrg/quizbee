<script lang="ts">
	import { BookOpen, X, Plus } from 'lucide-svelte';

	interface Props {
		topics: string[];
	}

	const { topics }: Props = $props();
</script>

<div class="card bg-base-100 shadow-lg">
	<div class="card-body">
		<h2 class="card-title text-lg">
			<BookOpen class="h-5 w-5" />
			Learning Topics
		</h2>
		<div class="flex flex-wrap gap-2">
			{#each topics as topic}
				<div class="badge badge-lg gap-2">
					{topic}
					<button class="hover:text-error">
						<X class="h-3 w-3" />
					</button>
				</div>
			{/each}
			<button class="badge badge-outline badge-lg gap-2">
				<Plus class="h-3 w-3" />
				Add Topic
			</button>
		</div>
		{#if topics.length === 0}
			<p class="text-sm opacity-70">Start taking quizzes to see your learning topics here!</p>
		{/if}
	</div>
</div>
