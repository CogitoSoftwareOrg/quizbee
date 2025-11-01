<script lang="ts">
    interface Props {
        size?: number;
        class?: string;
    }

    let { size = 28, class: className = "" }: Props = $props();
</script>

<svg 
    xmlns="http://www.w3.org/2000/svg" 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    stroke-width="2" 
    stroke-linecap="round" 
    stroke-linejoin="round" 
    class="text-base-content/60 cursor-pointer transition-colors duration-200 hover:text-base-content {className}"
>
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 16v-4"/>
    <path d="M12 8h.01"/>
</svg>