<script lang="ts">
	import type { ClassValue } from 'svelte/elements';
	import type { Snippet } from 'svelte';

	interface Props {
		el?: HTMLTextAreaElement;
		class?: ClassValue;
		name?: string;
		disabled?: boolean;
		ghost?: boolean;
		grow?: boolean;
		required?: boolean;
		placeholder?: string;
		rows?: number;
		resize?: 'none' | 'vertical' | 'horizontal' | 'both';
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
		value?: string;
		oninput?: (e: Event) => void;
		onblur?: (e: FocusEvent) => void;
		onfocus?: (e: FocusEvent) => void;
		onkeydown?: (e: KeyboardEvent) => void;
		onkeyup?: (e: KeyboardEvent) => void;
		onkeypress?: (e: KeyboardEvent) => void;
		onchange?: (e: Event) => void;
		children?: Snippet;
	}
	let {
		el = $bindable(),
		class: className = '',
		ghost = false,
		grow = false,
		color = 'neutral',
		size = 'md',
		value = $bindable(),
		disabled = false,
		rows = 4,
		placeholder = '',
		resize = 'none',
		required = false,
		name,
		oninput,
		onblur,
		onfocus,
		onkeydown,
		onkeyup,
		onkeypress,
		onchange,
		children
	}: Props = $props();

	const colorClasses = {
		primary: 'textarea-primary',
		secondary: 'textarea-secondary',
		accent: 'textarea-accent',
		info: 'textarea-info',
		success: 'textarea-success',
		warning: 'textarea-warning',
		error: 'textarea-error',
		neutral: 'textarea-neutral'
	};

	const sizeClasses = {
		xs: 'textarea-xs',
		sm: 'textarea-sm',
		md: 'textarea-md',
		lg: 'textarea-lg',
		xl: 'textarea-xl'
	};

	const resizeClasses = {
		none: 'resize-none',
		vertical: 'resize-y',
		horizontal: 'resize-x',
		both: 'resize'
	};
</script>

<label>
	{#if children}
		<p class="label font-semibold">{@render children()}</p>
	{/if}

	<textarea
		bind:this={el}
		class={[
			'textarea',
			ghost && 'textarea-ghost',
			colorClasses[color],
			sizeClasses[size],
			resizeClasses[resize],
			className
		]}
		{name}
		{disabled}
		{required}
		{placeholder}
		bind:value
		oninput={(e: Event) => {
			if (grow) {
				const textarea = e.target as HTMLTextAreaElement;
				textarea.style.height = 'auto';
				textarea.style.height = textarea.scrollHeight + 'px';
			}
			oninput?.(e);
		}}
		{onblur}
		{onfocus}
		{onkeydown}
		{onkeyup}
		{onkeypress}
		{onchange}
		{rows}
	></textarea>
</label>
