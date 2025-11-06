<script lang="ts">
	import { env } from '$env/dynamic/public';

	import { Shield, FileText } from 'lucide-svelte';
	import { PUBLIC_WEB_URL } from '$env/static/public';
</script>

<div class="card bg-base-100 shadow-lg">
	<div class="card-body">
		<div class="flex items-center justify-between">
			<span class="text-sm font-semibold">Legal</span>
		</div>

		<div class="-ml-4 mt-3 flex flex-col gap-1">
			<a
				href={`${env.PUBLIC_WEB_URL}legal/privacy-policy`}
				target="_blank"
				rel="noopener noreferrer"
				class="btn btn-ghost btn-sm justify-start gap-2"
			>
				<Shield class="h-4 w-4" />
				Privacy Policy
			</a>
			<a
				href={`${env.PUBLIC_WEB_URL}legal/terms-and-conditions`}
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
