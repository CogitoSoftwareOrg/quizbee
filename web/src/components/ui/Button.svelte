<script lang="ts">
	import type { ClassValue } from 'svelte/elements';
	import type { Snippet } from 'svelte';

	interface Props {
		class?: ClassValue;
		onclick?: (e: MouseEvent) => void;
		href?: string;
		color?:
			| 'primary'
			| 'secondary'
			| 'accent'
			| 'info'
			| 'success'
			| 'warning'
			| 'error'
			| 'neutral';
		style?: 'solid' | 'outline' | 'ghost' | 'link' | 'dash' | 'soft';
		size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
		type?: 'button' | 'submit' | 'reset';
		disabled?: boolean;
		active?: boolean;
		block?: boolean;
		square?: boolean;
		circle?: boolean;
		wide?: boolean;
		children: Snippet;
	}

	const {
		href,
		onclick,
		children,
		color = 'primary',
		style = 'solid',
		size = 'md',
		type = 'button',
		disabled = false,
		active = false,
		block = false,
		square = false,
		circle = false,
		wide = false,
		class: className = ''
	}: Props = $props();

	const colorClasses = {
		primary: 'btn-primary',
		secondary: 'btn-secondary',
		accent: 'btn-accent',
		info: 'btn-info',
		success: 'btn-success',
		warning: 'btn-warning',
		error: 'btn-error',
		neutral: 'btn-neutral'
	};

	const styleClasses = {
		solid: 'btn-solid',
		outline: 'btn-outline',
		ghost: 'btn-ghost',
		link: 'btn-link',
		dash: 'btn-dash',
		soft: 'btn-soft'
	};

	const sizeClasses = {
		xs: 'btn-xs',
		sm: 'btn-sm',
		md: 'btn-md',
		lg: 'btn-lg',
		xl: 'btn-xl'
	};
</script>

{#if href}
	<a
		{href}
		class={[
			'btn',
			colorClasses[color],
			styleClasses[style],
			sizeClasses[size],
			disabled && 'btn-disabled',
			active && 'btn-active',
			block && 'btn-block',
			square && 'btn-square',
			circle && 'btn-circle',
			wide && 'btn-wide',
			className
		]}
	>
		{@render children()}
	</a>
{:else}
	<button
		{type}
		{onclick}
		{disabled}
		class={[
			'btn',
			colorClasses[color],
			styleClasses[style],
			sizeClasses[size],
			disabled && 'btn-disabled',
			active && 'btn-active',
			block && 'btn-block',
			square && 'btn-square',
			circle && 'btn-circle',
			wide && 'btn-wide',
			className
		]}
	>
		{@render children()}
	</button>
{/if}
