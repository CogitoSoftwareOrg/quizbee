<script lang="ts">
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { userStore } from '$lib/apps/users/user.svelte';
	import type { UserExpand, UsersResponse } from '$lib/pb';

  interface Props {
    userLoadPromise: Promise<UsersResponse<unknown, UserExpand> | null>;
  }

  const { userLoadPromise }: Props = $props();


  const user = $derived(userStore.user);

    $effect(() => {
        const userId = user?.id;
        if (!userId) return;

        userStore.subscribe(userId);
        materialsStore.subscribe(userId);
        quizAttemptsStore.subscribe(userId);
        quizesStore.subscribe(userId);

        return () => {
            userStore.unsubscribe(userId);
            materialsStore.unsubscribe();
            quizAttemptsStore.unsubscribe();
            quizesStore.unsubscribe();
        };
    });
</script>