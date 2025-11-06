<script lang="ts">
  import { onMount } from "svelte";

  onMount(() => {
    console.log("Popup mounted");
  });

  let count = $state(0);
</script>

<main style="min-width:280px;min-height:160px;padding:12px">
  <h3>Svelte Popup</h3>
  <button onclick={() => count++}>Clicked {count} times</button>
</main>
