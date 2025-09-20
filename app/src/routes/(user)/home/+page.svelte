<script lang="ts">
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';
</script>

<div>
	{quizesStore.quizes.length}
</div>

<a href="/profile">Profile</a>
<a href="/quiz-attempts/7cpjsn5q9d60qix">Quiz Attempts</a>
<a href="/quizes/create">Create Quiz</a>
