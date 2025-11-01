<script lang="ts">
	import type { ClassValue } from 'svelte/elements';
	import type { Snippet } from 'svelte';

	interface Props {
		el?: HTMLInputElement;
		class?: ClassValue;
		name?: string;
		disabled?: boolean;
		ghost?: boolean;
		required?: boolean;
		accept?: string;
		multiple?: boolean;
		color?:
			| 'primary'
			| 'secondary'
			| 'accent'
			| 'info'
			| 'success'
			| 'warning'
			| 'error'
			| 'neutral';
		size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
		onchange?: (e: Event) => void;
		oninput?: (e: Event) => void;
		children?: Snippet;
	}
	let {
		el = $bindable(),
		class: className = '',
		ghost = false,
		color = 'primary',
		size = 'md',
		disabled = false,
		required = false,
		name,
		accept,
		multiple = false,
		onchange,
		oninput,
		children
	}: Props = $props();

	const colorClasses = {
		primary: 'file-input-primary',
		secondary: 'file-input-secondary',
		accent: 'file-input-accent',
		info: 'file-input-info',
		success: 'file-input-success',
		warning: 'file-input-warning',
		error: 'file-input-error',
		neutral: 'file-input-neutral'
	};

	const sizeClasses = {
		xs: 'file-input-xs',
		sm: 'file-input-sm',
		md: 'file-input-md',
		lg: 'file-input-lg',
		xl: 'file-input-xl'
	};
</script>

<label>
	{#if children}
		<p class="label block">{@render children()}</p>
	{/if}

	<input
		bind:this={el}
		type="file"
		class={[
			'file-input',
			ghost && 'file-input-ghost',
			colorClasses[color],
			sizeClasses[size],
			className
		]}
		{name}
		{disabled}
		{required}
		{accept}
		{multiple}
		{onchange}
		{oninput}
	/>
</label>
