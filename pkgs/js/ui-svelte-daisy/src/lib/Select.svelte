<script lang="ts">
	import type { ClassValue } from 'svelte/elements';
	import type { Snippet } from 'svelte';

	interface Props {
		class?: ClassValue;
		onchange?: (e: Event) => void;
		value?: string;
		disabled?: boolean;
		size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
		color?:
			| 'primary'
			| 'secondary'
			| 'neutral'
			| 'accent'
			| 'info'
			| 'success'
			| 'warning'
			| 'error';
		ghost?: boolean;
		options?: { value: string; label: string }[];
		children?: Snippet;
	}

	let {
		class: className = '',
		children,
		onchange,
		value = $bindable(),
		options = [],
		size = 'md',
		color = 'neutral',
		ghost = false,
		disabled = false
	}: Props = $props();

	const sizesMap = {
		xs: 'select-xs',
		sm: 'select-sm',
		md: 'select-md',
		lg: 'select-lg',
		xl: 'select-xl'
	};

	const colorClasses = {
		primary: 'select-primary',
		secondary: 'select-secondary',
		neutral: 'select-neutral',
		accent: 'select-accent',
		info: 'select-info',
		success: 'select-success',
		warning: 'select-warning',
		error: 'select-error'
	};
</script>

<select
	bind:value
	class={['select', sizesMap[size], colorClasses[color], ghost && 'select-ghost', className]}
	{disabled}
	onchange={(e) => {
		onchange?.(e);
	}}
>
	{#if children}
		<option value="">{@render children()}</option>
	{/if}
	{#each options as option}
		<option value={option.value}>{option.label}</option>
	{/each}
</select>
