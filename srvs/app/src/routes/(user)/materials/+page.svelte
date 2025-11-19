<script lang="ts">
	import { userStore } from '$lib/apps/users/user.svelte';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import MyMaterials from '$lib/apps/materials/MyMaterials.svelte';

	const user = $derived(userStore.user);
	const materials = $derived(materialsStore.materials);
</script>

<svelte:head>
	<title>Materials</title>
</svelte:head>

<div class="mx-auto flex h-full max-w-6xl flex-col items-center justify-center gap-4">
	{#if user}
		<MyMaterials class="w-full flex-1 px-5" {materials} userId={user.id} />
	{/if}
</div>
