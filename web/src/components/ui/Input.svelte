<script lang="ts">
	import type { ClassValue } from 'svelte/elements';
	import type { Snippet } from 'svelte';

	interface Props {
		class?: ClassValue;
		disabled?: boolean;
		placeholder?: string;
		ghost?: boolean;
		required?: boolean;
		name?: string;
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
		type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search';
		labelPosition?: 'right' | 'left';
		labelFloat?: boolean;
		value?: string;
		oninput?: (e: Event) => void;
		onblur?: (e: FocusEvent) => void;
		onfocus?: (e: FocusEvent) => void;
		onkeydown?: (e: KeyboardEvent) => void;
		onkeyup?: (e: KeyboardEvent) => void;
		onkeypress?: (e: KeyboardEvent) => void;
		onchange?: (e: Event) => void;
		children?: Snippet;
		legend?: string;
	}
	let {
		class: className = '',
		ghost = false,
		required = false,
		name,
		color = 'neutral',
		size = 'md',
		type = 'text',
		value = $bindable(),
		disabled = false,
		placeholder = '',
		oninput,
		onblur,
		onfocus,
		onkeydown,
		onkeyup,
		onkeypress,
		onchange,
		children,
		legend,
		labelPosition = 'left',
		labelFloat = false
	}: Props = $props();

	const colorClasses = {
		primary: 'input-primary',
		secondary: 'input-secondary',
		accent: 'input-accent',
		info: 'input-info',
		success: 'input-success',
		warning: 'input-warning',
		error: 'input-error',
		neutral: 'input-neutral'
	};

	const sizeClasses = {
		xs: 'input-xs',
		sm: 'input-sm',
		md: 'input-md',
		lg: 'input-lg',
		xl: 'input-xl'
	};
</script>

<fieldset>
	{#if legend}
		<legend class="fieldset-legend opacity-60">{legend}</legend>
	{/if}

	<label
		class={[
			'input',
			labelFloat && 'label-float',
			ghost && 'input-ghost',
			colorClasses[color],
			sizeClasses[size],
			className
		]}
	>
		{#if labelPosition === 'left' && children}
			{@render children()}
		{/if}

		<input
			class="grow outline-none ring-0"
			{name}
			{type}
			{required}
			{disabled}
			{placeholder}
			bind:value
			{oninput}
			{onblur}
			{onfocus}
			{onkeydown}
			{onkeyup}
			{onkeypress}
			{onchange}
		/>

		{#if labelPosition === 'right' && children}
			{@render children()}
		{/if}
	</label>
</fieldset>
