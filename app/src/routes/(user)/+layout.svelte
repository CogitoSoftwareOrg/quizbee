<script lang="ts">
	import { userStore } from '$lib/apps/users/user.svelte';
	import type { UsersResponse } from '$lib/pb/pocketbase-types';
	import type { UserExpand } from '$lib/pb/expands';

	const { data, children } = $props();

	const user = $derived(userStore.user);

	// wait for user to be loaded
	// $effect(() => {
	// 	data.userPromise.then((user) => {
	// 		userStore.user = user as unknown as UsersResponse<UserExpand>;
	// 	});
	// });

	// $effect(() => {
	// 	userStore.subscribe(user?.id || '');
	// });
</script>

{@render children?.()}
{JSON.stringify(user)}
