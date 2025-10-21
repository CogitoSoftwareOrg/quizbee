<script lang="ts">
	import { Target, Edit, Save } from 'lucide-svelte';

	interface Props {
		weeklyQuestionCount: number;
		weeklyProgress: number;
	}

	const { weeklyQuestionCount, weeklyProgress }: Props = $props();

	let weeklyGoal = $state(200);
	let editingGoal = $state(false);
</script>

<div class="card bg-base-100 shadow-lg">
	<div class="card-body">
		<h2 class="card-title text-lg">
			<Target class="h-5 w-5" />
			Weekly Learning Goal
		</h2>
		<div class="space-y-3">
			<div class="flex items-center justify-between">
				<div>
					<div class="text-sm font-semibold">
						{weeklyQuestionCount} / {weeklyGoal} questions
					</div>
					<div class="text-xs opacity-70">
						{weeklyProgress >= 100
							? '🎉 Goal achieved!'
							: `${weeklyGoal - weeklyQuestionCount} more to go`}
					</div>
				</div>
				<!-- {#if !editingGoal}
					<button onclick={() => (editingGoal = true)} class="btn btn-ghost btn-sm">
						<Edit class="h-3.5 w-3.5" />
					</button>
				{/if} -->
			</div>

			{#if editingGoal}
				<div class="flex items-center gap-2">
					<input
						type="number"
						bind:value={weeklyGoal}
						min="50"
						max="1000"
						step="50"
						class="input input-bordered input-sm flex-1"
					/>
					<button onclick={() => (editingGoal = false)} class="btn btn-primary btn-sm">
						<Save class="h-3.5 w-3.5" />
					</button>
				</div>
			{/if}

			<div class="relative">
				<progress class="progress progress-primary w-full" value={weeklyProgress} max="100"
				></progress>
				<div class="absolute right-0 top-0 -mt-5 text-xs font-semibold opacity-70">
					{weeklyProgress}%
				</div>
			</div>
		</div>
	</div>
</div>
