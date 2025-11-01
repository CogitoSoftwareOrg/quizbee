<script lang="ts">
	import type { Snippet } from 'svelte';
	import { Tween } from 'svelte/motion';

	interface Props {
		open: boolean;
		children: Snippet;
		sidebar: Snippet;
		side?: 'left' | 'right';
	}

	const { open = $bindable(), children, sidebar, side = 'left' }: Props = $props();

	const asideWidth = new Tween(0, { duration: 200 });

	$effect(() => {
		if (open) {
			asideWidth.set(100);
		} else {
			asideWidth.set(0);
		}
	});
</script>

<div class="flex h-full">
	<aside style:width={`${asideWidth.current}px`} class="flex-1" class:order-last={side === 'right'}>
		{@render sidebar()}
	</aside>

	<div class="flex-1">
		{@render children()}
	</div>
</div>
