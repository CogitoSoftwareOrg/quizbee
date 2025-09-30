<script lang="ts">
	let { value = $bindable(10) }: { value: number } = $props();
</script>

<div class="flex items-center justify-center gap-13">
	<label class="flex cursor-pointer flex-col items-center gap-2">
		<input
			type="radio"
			bind:group={value}
			value={10}
			class="radio radio-lg"
			style="--chkbg: #000; --chkfg: #fff;"
		/>
		<span class="text-md font-medium">10</span>
	</label>

	<label class="flex cursor-pointer flex-col items-center gap-2">
		<input
			type="radio"
			bind:group={value}
			value={20}
			class="radio radio-lg"
			style="--chkbg: #000; --chkfg: #fff;"
		/>
		<span class="text-md font-medium">20</span>
	</label>

	<label class="flex cursor-pointer flex-col items-center gap-2">
		<input
			type="radio"
			bind:group={value}
			value={30}
			class="radio radio-lg"
			style="--chkbg: #000; --chkfg: #fff;"
		/>
		<span class="text-md font-medium">30</span>
	</label>

	<label class="flex cursor-pointer flex-col items-center gap-2">
		<input
			type="radio"
			bind:group={value}
			value={50}
			class="radio radio-lg"
			style="--chkbg: #000; --chkfg: #fff;"
		/>
		<span class="text-md font-medium">50</span>
	</label>
</div>
