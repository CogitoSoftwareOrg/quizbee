<script lang="ts">
	import { Shield, FileText } from 'lucide-svelte';
</script>

<div class="card bg-base-100 shadow-lg">
	<div class="card-body">
		<div class="flex items-center justify-between">
			<span class="text-sm font-semibold">Legal</span>
		</div>

		<div class="mt-3 -ml-4 flex flex-col gap-1">
			<a
				href="https://quizbee.academy/legal/privacy-policy"
				target="_blank"
				rel="noopener noreferrer"
				class="btn btn-ghost btn-sm justify-start gap-2"
			>
				<Shield class="h-4 w-4" />
				Privacy Policy
			</a>
			<a
				href="https://quizbee.academy/legal/terms-and-conditions"
				target="_blank"
				rel="noopener noreferrer"
				class="btn btn-ghost btn-sm justify-start gap-2"
			>
				<FileText class="h-4 w-4" />
				Terms and Conditions
			</a>
		</div>
	</div>
</div>
