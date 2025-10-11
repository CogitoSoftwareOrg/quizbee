<script lang="ts">
	import { BookOpen } from 'lucide-svelte';

	interface Props {
		totalQuizzes: number;
		class?: string;
	}

	const { totalQuizzes, class: className = '' }: Props = $props();
</script>

<div class="card bg-base-100 shadow {className}">
	<div class="card-body p-4">
		<div class="flex items-center gap-2">
			<BookOpen class="text-secondary h-5 w-5" />
			<span class="text-xs font-semibold opacity-70">Completed</span>
		</div>
		<div class="mt-1">
			<div class="text-2xl font-bold">{totalQuizzes}</div>
			<div class="text-xs opacity-60">{totalQuizzes === 1 ? 'quiz' : 'quizzes'}</div>
		</div>
	</div>
</div>
