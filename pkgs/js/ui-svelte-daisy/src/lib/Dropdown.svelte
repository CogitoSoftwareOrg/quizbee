<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { ClassValue } from 'svelte/elements';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';

	import { clickOutside } from './actions/click-outside.js';
	import Button from './Button.svelte';

	interface Props {
		options: {
			label: string;
			value: string;
		}[];
		open?: boolean;
		selected?: string;
		class?: ClassValue;
		onclose?: () => void;
		onselect?: (value: string) => void;
		children?: Snippet;
		badge?: Snippet;

		mainActions?: Snippet<[string]>;
		rowActions?: Snippet<[string, boolean]>;
		endActions?: Snippet;
	}
	let {
		open = $bindable(false),
		options,
		selected,
		class: className,
		onclose,
		onselect,
		children,
		badge,
		mainActions,
		rowActions,
		endActions
	}: Props = $props();

	const selectedOption = $derived(options.find((o) => o.value === selected));

	function close() {
		open = false;
		onclose?.();
	}
</script>

<details
	bind:open
	use:clickOutside={{
		callback: close
	}}
	class={['dropdown relative', className]}
>
	<summary class="btn btn-block btn-ghost justify-between">
		<div class="flex min-w-0 flex-1 items-center gap-2">
			{@render badge?.()}

			{#if selectedOption}
				<span class="truncate font-semibold">{selectedOption.label}</span>
			{:else if children}
				<span class="truncate font-semibold">{@render children()}</span>
			{/if}
		</div>

		<div class="flex flex-shrink-0 items-center gap-1">
			{#if mainActions}
				{@render mainActions?.(selectedOption?.value || '')}
			{:else if rowActions}
				{@render rowActions?.(selectedOption?.value || '', false)}
			{:else}
				<ChevronDown size={14} />
			{/if}
		</div>
	</summary>

	<ul class="dropdown-content menu bg-base-100 rounded-box mt-1 w-full shadow">
		<div class="max-h-80 max-w-full overflow-y-auto">
			{#each options as option}
				<Button
					color={option.value === selected ? 'primary' : 'neutral'}
					style="ghost"
					class={[
						'w-full justify-between',
						option.value === selected && 'text-primary hover:text-black'
					]}
					onclick={() => {
						onselect?.(option.value);
					}}
				>
					<div class="flex min-w-0 flex-1 items-center">
						<span class="truncate font-semibold">{option.label}</span>
					</div>

					<div class="flex flex-shrink-0 items-center gap-1">
						{@render rowActions?.(option.value, option.value === selected)}
					</div>
				</Button>
			{/each}
		</div>

		{@render endActions?.()}
	</ul>
</details>
