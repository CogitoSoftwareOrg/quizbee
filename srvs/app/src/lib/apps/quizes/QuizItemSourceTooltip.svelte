<script lang="ts">
	import SearchSourceIcon from '$lib/assets/icons/search_source.svg';
	import type { UsedChunk } from './types';

	interface Props {
		usedChunks: UsedChunk[] | null | undefined;
		itemDecision: any;
	}

	const { usedChunks, itemDecision }: Props = $props();

	const shouldShow = $derived(!!itemDecision && usedChunks && usedChunks.length > 0);
</script>

{#if shouldShow}
	<div class="dropdown dropdown-end dropdown-bottom dropdown-hover">
		<div tabindex="0" role="button" class="btn btn-circle btn-ghost btn-sm">
			<img src={SearchSourceIcon} alt="Source" width="24" height="24" class="opacity-60" />
		</div>
		<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
		<div
			tabindex="0"
			class="dropdown-content z-50 card card-compact w-64 bg-base-200 text-base-content shadow border border-base-300"
		>
			<div class="card-body">
				<h3 class="card-title text-md">Source Material</h3>
				<ul class="space-y-2 text-xs">
					{#each usedChunks || [] as chunk}
						<li>
							<span class="block font-medium">{chunk.title}</span>
							{#if chunk.page}
								<span class="text-base-content/60">Page {chunk.page}</span>
							{/if}
						</li>
					{/each}
				</ul>
			</div>
		</div>
	</div>
{/if}
