<script lang="ts">
	import X from 'lucide-svelte/icons/x';
	import type { ClassValue } from 'svelte/elements';

	import { portal } from './actions/portal.js';

	import Button from './Button.svelte';

	interface Props {
		open?: boolean;
		portalId?: string;
		class?: ClassValue;
		children?: any;
		onclose?: () => void;
		backdrop?: boolean;
		noPadding?: boolean;
		placement?: 'top' | 'bottom' | 'left' | 'right' | 'center';
		order?: number;
		transparent?: boolean;

		transition?: boolean;
		id?: string;
		fullHeight?: boolean;
	}

	let {
		open = $bindable(false),
		portalId = 'body',
		class: className = '',
		children,
		onclose,
		placement = 'center',
		backdrop = false,
		noPadding = false,
		transparent = false,
		id,
		fullHeight = false
	}: Props = $props();

	let dialogElement: HTMLDialogElement | null = $state(null);

	let placementClass = $derived.by(() => {
		switch (placement) {
			case 'top':
				return 'modal-top';
			case 'bottom':
				return 'modal-bottom';
			case 'left':
				return 'modal-start';
			case 'right':
				return 'modal-end';
			case 'center':
				return 'modal-middle';
		}
	});

	function handleClose() {
		open = false;
		dialogElement?.close();
		onclose?.();
	}

	$effect(() => {
		if (!dialogElement) return;
		if (open) {
			dialogElement.showModal();
		} else {
			handleClose();
		}
	});
</script>

<div use:portal={portalId}>
	<dialog
		{id}
		style={transparent ? 'background: transparent' : ''}
		bind:this={dialogElement}
		class={['modal', placementClass]}
	>
		<div class={['modal-box relative', noPadding && 'p-0', className]}>
			<div class="absolute right-2 top-2 z-50">
				<Button color="neutral" style="ghost" onclick={handleClose} circle>
					<X size={24} />
				</Button>
			</div>

			<div
				class={[
					'overflow-y-auto',
					fullHeight ? 'max-h-screen' : 'max-h-[calc(100vh-8rem)]',
					!noPadding && 'pr-2'
				]}
			>
				{@render children()}
			</div>
		</div>

		{#if backdrop}
			<form method="dialog" class="modal-backdrop">
				<button onclick={handleClose}>close</button>
			</form>
		{/if}
	</dialog>
</div>
