<script lang="ts">
	import SearchSourceIcon from '$lib/assets/icons/search_source.svg';
	import type { UsedChunk } from './types';

	interface Props {
		usedChunks: UsedChunk[] | null | undefined;
		itemDecision: any;
	}

	const { usedChunks, itemDecision }: Props = $props();

	const shouldShow = $derived(!!itemDecision && usedChunks && usedChunks.length > 0);

	const groupedChunks = $derived(() => {
		if (!usedChunks) return [];
		const grouped = new Map<string, number[]>();
		for (const chunk of usedChunks) {
			const pages = grouped.get(chunk.title) || [];
			if (chunk.pages) {
				for (const page of chunk.pages) {
					if (!pages.includes(page)) {
						pages.push(page);
					}
				}
			}
			grouped.set(chunk.title, pages);
		}
		return Array.from(grouped.entries()).map(([title, pages]) => ({
			title,
			pages: pages.sort((a, b) => a - b)
		}));
	});
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
					{#each groupedChunks() as chunk}
						<li>
							<span class="block font-medium">{chunk.title}</span>
							{#if chunk.pages && chunk.pages.length == 1}
								<span class="text-base-content/60">Page {chunk.pages[0]}</span>
							{:else if chunk.pages && chunk.pages.length > 1}
								<span class="text-base-content/60">Pages {chunk.pages.join(', ')}</span>
							{/if}
						</li>
					{/each}
				</ul>
			</div>
		</div>
	</div>
{/if}
