<script lang="ts">
  import { onMount } from "svelte";

  let accepted = $state(false);

  onMount(() => {
    accepted = localStorage.getItem("okCookies") === "true";
  });
</script>

{#if !accepted}
  <div class="toast toast-start">
    <div
      class="alert px-4 py-3 shadow-lg border-secondary rounded-xl flex flex-col"
    >
      <span class="text-lg font-semibold">We use cookies</span>
      <a class="link link-hover font-bold" href="/legal/privacy-policy"
        >Privacy Policy</a
      >
      <button
        class="self-start btn btn-primary btn-lg"
        onclick={() => {
          localStorage.setItem("okCookies", "true");
          accepted = true;
        }}
      >
        Ok
      </button>
    </div>
  </div>
{/if}
