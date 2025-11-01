<script lang="ts">
	import Modal from '$lib/Modal.svelte';
	import Button from '$lib/Button.svelte';
	import Card from '$lib/Card.svelte';
	import Input from '$lib/Input.svelte';

	let modalCenter = $state(false);
	let modalTop = $state(false);
	let modalBottom = $state(false);
	let modalLeft = $state(false);
	let modalRight = $state(false);
	let modalLongContent = $state(false);
	let modalWithCards = $state(false);
	let modalWithForm = $state(false);
	let modalNoPadding = $state(false);
	let modalBackdrop = $state(false);
</script>

<div class="container mx-auto p-8">
	<h1 class="mb-8 text-4xl font-bold">Modal Showcase</h1>

	<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
		<!-- Basic Modal -->
		<Card>
			<div class="card-body">
				<h2 class="card-title">Basic Modal (Center)</h2>
				<p>Standard modal in center with short content</p>
				<Button onclick={() => (modalCenter = true)}>Open Center Modal</Button>
			</div>
		</Card>

		<!-- Top Modal -->
		<Card>
			<div class="card-body">
				<h2 class="card-title">Top Modal</h2>
				<p>Modal positioned at the top</p>
				<Button onclick={() => (modalTop = true)}>Open Top Modal</Button>
			</div>
		</Card>

		<!-- Bottom Modal -->
		<Card>
			<div class="card-body">
				<h2 class="card-title">Bottom Modal</h2>
				<p>Modal positioned at the bottom</p>
				<Button onclick={() => (modalBottom = true)}>Open Bottom Modal</Button>
			</div>
		</Card>

		<!-- Left Modal -->
		<Card>
			<div class="card-body">
				<h2 class="card-title">Left Modal</h2>
				<p>Modal positioned on the left</p>
				<Button onclick={() => (modalLeft = true)}>Open Left Modal</Button>
			</div>
		</Card>

		<!-- Right Modal -->
		<Card>
			<div class="card-body">
				<h2 class="card-title">Right Modal</h2>
				<p>Modal positioned on the right</p>
				<Button onclick={() => (modalRight = true)}>Open Right Modal</Button>
			</div>
		</Card>

		<!-- Long Content Modal -->
		<Card>
			<div class="card-body">
				<h2 class="card-title">Scrollable Content</h2>
				<p>Modal with very long content to test scrolling</p>
				<Button color="primary" onclick={() => (modalLongContent = true)}>
					Open Scrollable Modal
				</Button>
			</div>
		</Card>

		<!-- Modal with Cards -->
		<Card>
			<div class="card-body">
				<h2 class="card-title">Modal with Cards</h2>
				<p>Modal containing multiple cards</p>
				<Button color="secondary" onclick={() => (modalWithCards = true)}>Open Cards Modal</Button>
			</div>
		</Card>

		<!-- Modal with Form -->
		<Card>
			<div class="card-body">
				<h2 class="card-title">Modal with Form</h2>
				<p>Modal with form elements</p>
				<Button color="accent" onclick={() => (modalWithForm = true)}>Open Form Modal</Button>
			</div>
		</Card>

		<!-- No Padding Modal -->
		<Card>
			<div class="card-body">
				<h2 class="card-title">No Padding Modal</h2>
				<p>Modal without padding</p>
				<Button color="info" onclick={() => (modalNoPadding = true)}>Open No Padding</Button>
			</div>
		</Card>

		<!-- Backdrop Modal -->
		<Card>
			<div class="card-body">
				<h2 class="card-title">Backdrop Modal</h2>
				<p>Modal with clickable backdrop to close</p>
				<Button color="success" onclick={() => (modalBackdrop = true)}>Open with Backdrop</Button>
			</div>
		</Card>
	</div>
</div>

<!-- Center Modal -->
<Modal bind:open={modalCenter}>
	<div class="p-4">
		<h3 class="mb-4 text-lg font-bold">Center Modal</h3>
		<p class="py-4">
			This is a standard modal positioned in the center. The close button should always be visible
			at the top right, even if content scrolls.
		</p>
		<p class="py-4">Some additional content to test the layout.</p>
	</div>
</Modal>

<!-- Top Modal -->
<Modal bind:open={modalTop} placement="top">
	<div class="p-4">
		<h3 class="mb-4 text-lg font-bold">Top Modal</h3>
		<p class="py-4">This modal is positioned at the top of the screen.</p>
		<p class="py-4">Notice how it appears from the top edge.</p>
	</div>
</Modal>

<!-- Bottom Modal -->
<Modal bind:open={modalBottom} placement="bottom">
	<div class="p-4">
		<h3 class="mb-4 text-lg font-bold">Bottom Modal</h3>
		<p class="py-4">This modal is positioned at the bottom of the screen.</p>
		<p class="py-4">Great for mobile-like bottom sheets!</p>
	</div>
</Modal>

<!-- Left Modal -->
<Modal bind:open={modalLeft} placement="left">
	<div class="p-4">
		<h3 class="mb-4 text-lg font-bold">Left Modal</h3>
		<p class="py-4">This modal slides in from the left.</p>
		<p class="py-4">Perfect for navigation menus or side panels.</p>
	</div>
</Modal>

<!-- Right Modal -->
<Modal bind:open={modalRight} placement="right">
	<div class="p-4">
		<h3 class="mb-4 text-lg font-bold">Right Modal</h3>
		<p class="py-4">This modal slides in from the right.</p>
		<p class="py-4">Commonly used for settings or filters.</p>
	</div>
</Modal>

<!-- Long Content Modal -->
<Modal bind:open={modalLongContent}>
	<div class="p-4">
		<h3 class="mb-4 text-lg font-bold">Scrollable Content Test</h3>
		<p class="mb-4">
			This modal has a lot of content to demonstrate scrolling. The close button (X) should remain
			fixed at the top right corner and never scroll away.
		</p>

		{#each Array(20) as _, i}
			<div class="bg-base-200 mb-4 rounded-lg p-4">
				<h4 class="font-semibold">Section {i + 1}</h4>
				<p>
					Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt
					ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
					ullamco laboris.
				</p>
			</div>
		{/each}

		<p class="bg-success text-success-content mt-4 rounded-lg p-4">
			✅ If you can see this and the X button is still visible at the top, scrolling works
			correctly!
		</p>
	</div>
</Modal>

<!-- Modal with Cards -->
<Modal bind:open={modalWithCards}>
	<div class="p-4">
		<h3 class="mb-4 text-lg font-bold">Modal with Multiple Cards</h3>
		<p class="mb-4">Testing how cards behave inside a scrollable modal.</p>

		{#each Array(8) as _, i}
			<Card class="mb-4">
				<div class="card-body">
					<h4 class="card-title">Card {i + 1}</h4>
					<p>
						This is a card inside a modal. The close button should remain visible above all cards.
					</p>
					<div class="card-actions justify-end">
						<Button size="sm" color="primary">Action</Button>
						<Button size="sm">Cancel</Button>
					</div>
				</div>
			</Card>
		{/each}
	</div>
</Modal>

<!-- Modal with Form -->
<Modal bind:open={modalWithForm}>
	<div class="p-4">
		<h3 class="mb-6 text-lg font-bold">User Registration Form</h3>

		<form class="space-y-4">
			<div>
				<label for="firstName" class="label">
					<span class="label-text">First Name</span>
				</label>
				<Input id="firstName" placeholder="John" />
			</div>

			<div>
				<label for="lastName" class="label">
					<span class="label-text">Last Name</span>
				</label>
				<Input id="lastName" placeholder="Doe" />
			</div>

			<div>
				<label for="email" class="label">
					<span class="label-text">Email</span>
				</label>
				<Input id="email" type="email" placeholder="john.doe@example.com" />
			</div>

			<div>
				<label for="password" class="label">
					<span class="label-text">Password</span>
				</label>
				<Input id="password" type="password" placeholder="••••••••" />
			</div>

			<div>
				<label for="bio" class="label">
					<span class="label-text">Bio</span>
				</label>
				<textarea
					id="bio"
					class="textarea textarea-bordered w-full"
					rows="4"
					placeholder="Tell us about yourself..."
				></textarea>
			</div>

			<div>
				<label for="country" class="label">
					<span class="label-text">Country</span>
				</label>
				<select id="country" class="select select-bordered w-full">
					<option>United States</option>
					<option>United Kingdom</option>
					<option>Canada</option>
					<option>Australia</option>
					<option>Germany</option>
					<option>France</option>
					<option>Japan</option>
				</select>
			</div>

			<div class="form-control">
				<label class="label cursor-pointer">
					<span class="label-text">Accept terms and conditions</span>
					<input type="checkbox" class="checkbox" />
				</label>
			</div>

			<div class="form-control">
				<label class="label cursor-pointer">
					<span class="label-text">Subscribe to newsletter</span>
					<input type="checkbox" class="checkbox" />
				</label>
			</div>

			<div class="flex justify-end gap-2 pt-4">
				<Button color="primary" type="submit">Register</Button>
				<Button onclick={() => (modalWithForm = false)}>Cancel</Button>
			</div>
		</form>
	</div>
</Modal>

<!-- No Padding Modal -->
<Modal bind:open={modalNoPadding} noPadding>
	<div class="relative">
		<img src="https://picsum.photos/800/600" alt="Placeholder" class="h-64 w-full object-cover" />
		<div class="p-6">
			<h3 class="mb-4 text-lg font-bold">No Padding Modal</h3>
			<p class="mb-4">
				This modal has no padding on the modal-box, allowing for full-width content like images or
				custom layouts.
			</p>

			{#each Array(10) as _, i}
				<div class="bg-base-200 mb-3 rounded p-3">
					<p>Scrollable content item {i + 1}</p>
				</div>
			{/each}
		</div>
	</div>
</Modal>

<!-- Backdrop Modal -->
<Modal bind:open={modalBackdrop} backdrop>
	<div class="p-4">
		<h3 class="mb-4 text-lg font-bold">Modal with Backdrop</h3>
		<p class="py-4">
			This modal has a backdrop. Click outside the modal or on the backdrop to close it.
		</p>
		<p class="py-4">You can also use the X button or press ESC key to close.</p>

		{#each Array(15) as _, i}
			<div class="bg-base-200 mb-3 rounded p-3">
				<p>Content section {i + 1}</p>
			</div>
		{/each}
	</div>
</Modal>
