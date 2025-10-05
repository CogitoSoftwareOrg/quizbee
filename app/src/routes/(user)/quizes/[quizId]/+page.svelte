<script lang="ts">
	import { page } from '$app/state';

	const quiz = $derived(page.data.pageQuiz);
</script>

<div>
	{quiz?.title}
</div>
