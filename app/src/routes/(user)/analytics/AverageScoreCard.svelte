<script lang="ts">
	import { TrendingUp } from 'lucide-svelte';

	interface Props {
		averageScore: number;
		limit?: number;
		class?: string;
	}

	const { averageScore, limit = 10, class: className = '' }: Props = $props();
</script>

<div class="card bg-base-100 shadow {className}">
	<div class="card-body p-4">
		<div class="flex items-center gap-2">
			<TrendingUp class="text-success h-5 w-5" />
			<span class="text-xs font-semibold opacity-70">Avg Score</span>
		</div>
		<div class="mt-1">
			<div class="text-2xl font-bold">{averageScore}%</div>
			<div class="text-xs opacity-60">last {limit}</div>
		</div>
	</div>
</div>
