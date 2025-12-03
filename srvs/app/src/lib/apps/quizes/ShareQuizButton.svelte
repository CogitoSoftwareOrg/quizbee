<script lang="ts">
	import { Share2, Copy, Check, Facebook, Twitter, MessageCircle } from 'lucide-svelte';
	// @ts-ignore
	import QRCode from 'qrcode';
	import { onMount } from 'svelte';

	import { Modal, Button } from '@quizbee/ui-svelte-daisy';
	import type { ClassValue } from 'svelte/elements';
	import { env } from '$env/dynamic/public';

	interface Props {
		quizId: string;
		quizTitle: string;
		category: string;
		baseUrl?: string;
		block?: boolean;
		class?: ClassValue;
	}

	const {
		quizId,
		quizTitle,
		category,
		baseUrl = env.PUBLIC_WEB_URL,
		block = false,
		class: className = ''
	}: Props = $props();

	let modalOpen = $state(false);
	let qrDataUrl = $state('');
	let copied = $state(false);

	const shareUrl = $derived(
		baseUrl
			? `${baseUrl}quizes/${category || 'general'}/${quizId}`
			: typeof window !== 'undefined'
				? `${window.location.origin}/quizes/${quizId}`
				: ''
	);

	const shareText = $derived(`Try this quiz: ${quizTitle}`);

	// Generate QR code on mount
	onMount(async () => {
		if (shareUrl) {
			try {
				qrDataUrl = await QRCode.toDataURL(shareUrl, {
					width: 256,
					margin: 2,
					errorCorrectionLevel: 'M',
					color: {
						dark: '#000000',
						light: '#FFFFFF'
					}
				});
			} catch (error) {
				console.error('Error generating QR code:', error);
			}
		}
	});

	// Copy link to clipboard
	async function copyToClipboard() {
		try {
			await navigator.clipboard.writeText(shareUrl);
			copied = true;
			setTimeout(() => {
				copied = false;
			}, 2000);
		} catch (error) {
			console.error('Failed to copy:', error);
		}
	}

	// Native sharing via Web Share API
	async function nativeShare() {
		if (navigator.share) {
			try {
				await navigator.share({
					title: quizTitle,
					text: shareText,
					url: shareUrl
				});
			} catch (error) {
				// User cancelled or error occurred
				console.log('Share cancelled or failed:', error);
			}
		}
	}

	// Social media sharing methods
	function openShareWindow(url: string, width = 600, height = 500) {
		const left = (screen.width - width) / 2;
		const top = (screen.height - height) / 2;
		const features = `width=${width},height=${height},left=${left},top=${top},toolbar=no,location=no,status=no,menubar=no,scrollbars=yes,resizable=yes`;
		window.open(url, '_blank', features);
	}

	function shareToFacebook() {
		const url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`;
		openShareWindow(url, 600, 500);
	}

	function shareToTwitter() {
		const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`;
		openShareWindow(url, 550, 420);
	}

	function shareToTelegram() {
		const url = `https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(shareText)}`;
		openShareWindow(url, 600, 500);
	}

	function shareToWhatsApp() {
		const url = `https://api.whatsapp.com/send?text=${encodeURIComponent(shareText + ' ' + shareUrl)}`;
		openShareWindow(url, 600, 500);
	}
</script>

<Button
	color="primary"
	style="solid"
	{block}
	class={className}
	onclick={() => {
		modalOpen = true;
	}}
>
	<Share2 size={16} />
	<span>Share</span>
</Button>

<Modal class="max-w-md" backdrop open={modalOpen} onclose={() => (modalOpen = false)}>
	<div class="flex flex-col gap-6 pt-8">
		<div class="text-center">
			<h3 class="text-xl font-bold">Share Quiz</h3>
			<p class="text-base-content/70 mt-2 text-sm">{quizTitle}</p>
		</div>

		<!-- QR Code -->
		{#if qrDataUrl}
			<div class="bg-base-200 flex items-center justify-center rounded-lg p-4">
				<img src={qrDataUrl} alt="QR code for quiz" class="h-64 w-64" />
			</div>
		{/if}

		<!-- URL Copy -->
		<div class="flex flex-col gap-2">
			<label for="share-url" class="text-sm font-medium">Quiz link:</label>
			<div class="flex gap-2">
				<input
					id="share-url"
					type="text"
					readonly
					value={shareUrl}
					class="input input-bordered flex-1 text-sm"
					onclick={(e) => e.currentTarget.select()}
				/>
				<Button color="primary" style="outline" onclick={copyToClipboard}>
					{#if copied}
						<Check size={20} class="text-success" />
					{:else}
						<Copy size={20} />
					{/if}
				</Button>
			</div>
		</div>

		<!-- Share Buttons -->
		<div class="flex flex-col gap-3">
			<p class="text-sm font-medium">Share via:</p>

			<!-- Native Share (if available) -->
			{#if typeof window !== 'undefined' && 'share' in navigator}
				<Button color="primary" style="solid" onclick={nativeShare} class="w-full">
					<Share2 size={20} />
					<span>Share...</span>
				</Button>
			{/if}

			<!-- Social Media Buttons -->
			<div class="grid grid-cols-2 gap-2">
				<Button color="neutral" style="outline" onclick={shareToTelegram} class="justify-start">
					<MessageCircle size={20} />
					<span>Telegram</span>
				</Button>

				<Button color="neutral" style="outline" onclick={shareToWhatsApp} class="justify-start">
					<MessageCircle size={20} />
					<span>WhatsApp</span>
				</Button>

				<Button color="neutral" style="outline" onclick={shareToFacebook} class="justify-start">
					<Facebook size={20} />
					<span>Facebook</span>
				</Button>

				<Button color="neutral" style="outline" onclick={shareToTwitter} class="justify-start">
					<Twitter size={20} />
					<span>Twitter</span>
				</Button>
			</div>
		</div>
	</div>
</Modal>
