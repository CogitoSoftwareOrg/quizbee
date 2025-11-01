<script lang="ts">
	interface Props {
		onkeydown: (event: KeyboardEvent) => void;
		keys?: string[];
	}

	let { keys, onkeydown }: Props = $props();

	function handleKeydown(event: KeyboardEvent) {
		if (keys && !keys.includes(event.key)) return;
		onkeydown(event);
	}

	$effect(() => {
		window.addEventListener('keydown', handleKeydown);

		return () => window.removeEventListener('keydown', handleKeydown);
	});
</script>
