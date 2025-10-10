<script lang="ts">
	import { Flame } from 'lucide-svelte';

	interface Props {
		streak: number;
		class?: string;
	}

	const { streak, class: className = '' }: Props = $props();
</script>

<div class="card bg-base-100 shadow {className}">
	<div class="card-body p-4">
		<div class="flex items-center gap-2">
			<Flame class="text-warning h-5 w-5" />
			<span class="text-xs font-semibold opacity-70">Streak</span>
		</div>
		<div class="mt-1">
			<div class="text-2xl font-bold">{streak}</div>
			<div class="text-xs opacity-60">{streak === 1 ? 'day' : 'days'}</div>
		</div>
	</div>
</div>
