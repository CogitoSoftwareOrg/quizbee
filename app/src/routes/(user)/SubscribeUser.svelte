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

  $effect(() => {
        userLoadPromise.then(async (userLoad) => {
            const materials = userLoad?.expand.materials_via_user || [];
            const quizAttempts = userLoad?.expand.quizAttempts_via_user || [];
            const quizes = userLoad?.expand.quizes_via_author || [];

            materialsStore.materials = materials;
            quizAttemptsStore.quizAttempts = quizAttempts;
            quizesStore.quizes = quizes;

            userLoad!.expand = {} as UserExpand;
            userStore.user = userLoad!;

            userStore.setLoaded();
        });
    });

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