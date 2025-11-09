<script lang="ts">
	import { Target } from 'lucide-svelte';

	interface Props {
		weeklyQuestionCount: number;
		class?: string;
	}

	const { weeklyQuestionCount, class: className = '' }: Props = $props();
</script>

<div class="card bg-base-100 shadow {className}">
	<div class="card-body p-3 sm:p-4">
		<div class="flex items-center gap-2">
			<Target class="text-primary h-4 w-4 sm:h-5 sm:w-5" />
			<span class="text-xs font-semibold opacity-70">This Week</span>
		</div>
		<div class="mt-0.5 sm:mt-1">
			<div class="text-xl font-bold sm:text-2xl">{weeklyQuestionCount}</div>
			<div class="text-xs opacity-60">questions</div>
		</div>
	</div>
</div>
