<script lang="ts">
	import type { ClassValue } from 'svelte/elements';
	import type { Snippet } from 'svelte';

	interface Props {
		class?: ClassValue;
		size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
		border?: 'none' | 'solid' | 'dash';
		title?: string;
		actions?: Snippet;
		children?: Snippet;
		image?: {
			src: string;
			alt: string;
			styles?: string;
			mode?: 'default' | 'side' | 'full';
		};
	}

	const {
		class: className,
		title,
		image,
		actions,
		children,
		size = 'md',
		border = 'none'
	}: Props = $props();

	const sizeClasses = {
		xs: 'card-xs',
		sm: 'card-sm',
		md: 'card-md',
		lg: 'card-lg',
		xl: 'card-xl'
	};

	const borderClasses = {
		none: '',
		solid: 'card-border',
		dash: 'card-dash'
	};

	const imageClasses = {
		default: '',
		side: 'card-side',
		full: 'card-full'
	};
</script>

<div
	class={[
		'card bg-base-100 w-full shadow-sm',
		sizeClasses[size],
		borderClasses[border],
		imageClasses[image?.mode || 'default'],
		className
	]}
>
	{#if image}
		<figure>
			<img src={image.src} alt={image.alt} class={image.styles} />
		</figure>
	{/if}
	<div class="card-body">
		{#if title}
			<h3 class="card-title">{title}</h3>
		{/if}

		{#if children}
			<div>
				{@render children()}
			</div>
		{/if}

		{#if actions}
			<div class="card-actions justify-end">
				{@render actions()}
			</div>
		{/if}
	</div>
</div>
