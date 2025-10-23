<script lang="ts">
	import posthog from 'posthog-js';
	import { Crown } from 'lucide-svelte';

	import { Modal, Button, TextArea } from '@cogisoft/ui-svelte-daisy';

	import { patchApi } from '$lib/api/call-api';
	import { subscriptionStore } from '$lib/apps/billing/subscriptions.svelte';
	import { uiStore } from '$lib/apps/users/ui.svelte';
	import {
		type QuizesResponse,
		type QuizAttemptsResponse,
		pb,
		type QuizItemsResponse
	} from '$lib/pb';

	interface Props {
		quiz: QuizesResponse;
		quizAttempt: QuizAttemptsResponse;
		item: QuizItemsResponse;
	}

	let { quiz, quizAttempt, item }: Props = $props();

	let showModal = $state(false);

	// Modal Form
	let difficulty: 'easier' | 'same' | 'harder' = $state('same');
	let topic: 'less' | 'same' | 'more' = $state('same');
	let additionalQuery = $state('');

	const sub = $derived(subscriptionStore.subscription);
	const isFreePlan = $derived(sub?.tariff === 'free');
</script>

<div class="mt-6 flex gap-2">
	<Button
		onclick={() => {
			if (isFreePlan) {
				uiStore.setPaywallOpen(true);
			} else {
				showModal = true;
			}
		}}
		class="flex-1"
		color="neutral"
		style="soft"
	>
		Manage Quiz
		<Crown size={16} />
	</Button>
</div>

<Modal backdrop bind:open={showModal}>
	<div class="flex flex-col gap-6 p-4">
		<h3 class="mb-2 text-center text-xl font-bold">Manage Quiz</h3>
		<div class="flex flex-col gap-2">
			<h4 class="text-lg font-medium">Difficulty</h4>
			<div class="flex gap-2">
				<Button
					size="lg"
					class="flex-1"
					color="success"
					style={difficulty === 'easier' ? 'solid' : 'soft'}
					onclick={() => {
						if (difficulty === 'easier') {
							difficulty = 'same';
						} else {
							difficulty = 'easier';
						}
					}}>Easier</Button
				>
				<!-- <Button
					class="flex-1"
					color="warning"
					style={difficulty === 'same' ? 'ghost' : 'soft'}
					onclick={() => (difficulty = 'same')}>Same</Button
				> -->
				<Button
					size="lg"
					class="flex-1"
					color="error"
					style={difficulty === 'harder' ? 'solid' : 'soft'}
					onclick={() => {
						if (difficulty === 'harder') {
							difficulty = 'same';
						} else {
							difficulty = 'harder';
						}
					}}>Harder</Button
				>
			</div>
		</div>

		<div class="flex flex-col gap-2">
			<h4 class="text-lg font-medium">This topic</h4>
			<div class="flex gap-2">
				<Button
					size="lg"
					class="flex-1"
					color="success"
					style={topic === 'less' ? 'solid' : 'soft'}
					onclick={() => {
						if (topic === 'less') {
							topic = 'same';
						} else {
							topic = 'less';
						}
					}}>Less</Button
				>
				<!-- <Button
					class="flex-1"
					color="warning"
					style={topic === 'same' ? 'ghost' : 'soft'}
					onclick={() => (topic = 'same')}>Same</Button
				> -->
				<Button
					size="lg"
					class="flex-1"
					color="error"
					style={topic === 'more' ? 'solid' : 'soft'}
					onclick={() => {
						if (topic === 'more') {
							topic = 'same';
						} else {
							topic = 'more';
						}
					}}>More</Button
				>
			</div>

			<div class="mt-2 flex flex-col gap-2">
				<h4 class="text-lg font-medium">Additional Query</h4>
				<TextArea
					class="w-full"
					bind:value={additionalQuery}
					placeholder="Enter additional query"
				/>
			</div>
		</div>

		<div class="mt-4 flex justify-end gap-2">
			<Button
				size="lg"
				onclick={async () => {
					showModal = false;
					if (item.managed) return;

					await pb!.collection('quizItems').update(item.id, {
						managed: true
					});

					const upd = { dynamicConfig: quiz.dynamicConfig } as any;

					if (difficulty === 'easier') {
						if (quiz.difficulty === 'beginner') {
							upd.dynamicConfig.extraBeginner.push(item.question);
						} else if (quiz.difficulty === 'intermediate') {
							upd.difficulty = 'beginner';
						} else if (quiz.difficulty === 'expert') {
							upd.difficulty = 'intermediate';
						}
					}

					if (difficulty === 'harder') {
						if (quiz.difficulty === 'expert') {
							upd.dynamicConfig.extraExpert.push(item.question);
						} else if (quiz.difficulty === 'intermediate') {
							upd.difficulty = 'expert';
						} else if (quiz.difficulty === 'beginner') {
							upd.difficulty = 'intermediate';
						}
					}

					if (topic === 'less') {
						upd.dynamicConfig.lessOnTopic.push(item.question);
					}
					if (topic === 'more') {
						upd.dynamicConfig.moreOnTopic.push(item.question);
					}

					if (additionalQuery) {
						upd.dynamicConfig.adds.push(additionalQuery);
					}

					console.log(upd);
					await pb!.collection('quizes').update(quiz.id, upd);

					posthog.capture('quiz_management_started', {
						quizId: quiz.id,
						quizAttemptId: quizAttempt.id,
						itemId: item.id,
						difficulty,
						topic,
						additionalQuery
					});
					await patchApi(`quizes/${quiz.id}`, {
						attempt_id: quizAttempt.id,
						limit: 5,
						mode: 'regenerate'
					});
				}}
				color="success"
				style="soft">Confirm (-5 questions)</Button
			>
		</div>
	</div>
</Modal>
