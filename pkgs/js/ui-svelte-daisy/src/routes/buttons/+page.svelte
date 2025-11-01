<script lang="ts">
	import { Button } from '$lib/index.js';
</script>

<div class="container mx-auto space-y-12 p-8">
	<div class="mb-12 text-center">
		<h1 class="mb-4 text-4xl font-bold">Button Component Preview</h1>
		<p class="text-lg text-gray-600">Explore different button variants, colors, sizes and styles</p>
	</div>

	<!-- Colors Section -->
	<section>
		<h2 class="mb-6 text-2xl font-semibold">Colors</h2>
		<div class="flex flex-wrap gap-4">
			<Button color="primary">Primary</Button>
			<Button color="secondary">Secondary</Button>
			<Button color="accent">Accent</Button>
			<Button color="info">Info</Button>
			<Button color="success">Success</Button>
			<Button color="warning">Warning</Button>
			<Button color="error">Error</Button>
			<Button color="neutral">Neutral</Button>
		</div>
	</section>

	<!-- Styles Section -->
	<section>
		<h2 class="mb-6 text-2xl font-semibold">Styles</h2>
		<div class="flex flex-wrap gap-4">
			<Button style="solid">Solid</Button>
			<Button style="outline">Outline</Button>
			<Button style="ghost">Ghost</Button>
			<Button style="link">Link</Button>
			<Button style="dash">Dash</Button>
			<Button style="soft">Soft</Button>
		</div>
	</section>

	<!-- Sizes Section -->
	<section>
		<h2 class="mb-6 text-2xl font-semibold">Sizes</h2>
		<div class="flex flex-wrap items-center gap-4">
			<Button size="xs">Extra Small</Button>
			<Button size="sm">Small</Button>
			<Button size="md">Medium</Button>
			<Button size="lg">Large</Button>
			<Button size="xl">Extra Large</Button>
		</div>
	</section>

	<!-- Color + Style Combinations -->
	<section>
		<h2 class="mb-6 text-2xl font-semibold">Color & Style Combinations</h2>
		<div class="grid grid-cols-2 gap-6 md:grid-cols-4">
			<div class="space-y-3">
				<h3 class="text-sm font-medium text-gray-600">Primary</h3>
				<Button color="primary" style="solid">Solid</Button>
				<Button color="primary" style="outline">Outline</Button>
				<Button color="primary" style="ghost">Ghost</Button>
			</div>
			<div class="space-y-3">
				<h3 class="text-sm font-medium text-gray-600">Success</h3>
				<Button color="success" style="solid">Solid</Button>
				<Button color="success" style="outline">Outline</Button>
				<Button color="success" style="ghost">Ghost</Button>
			</div>
			<div class="space-y-3">
				<h3 class="text-sm font-medium text-gray-600">Warning</h3>
				<Button color="warning" style="solid">Solid</Button>
				<Button color="warning" style="outline">Outline</Button>
				<Button color="warning" style="ghost">Ghost</Button>
			</div>
			<div class="space-y-3">
				<h3 class="text-sm font-medium text-gray-600">Error</h3>
				<Button color="error" style="solid">Solid</Button>
				<Button color="error" style="outline">Outline</Button>
				<Button color="error" style="ghost">Ghost</Button>
			</div>
		</div>
	</section>

	<!-- States Section -->
	<section>
		<h2 class="mb-6 text-2xl font-semibold">States</h2>
		<div class="flex flex-wrap gap-4">
			<Button>Normal</Button>
			<Button active={true}>Active</Button>
			<Button disabled={true}>Disabled</Button>
			<Button color="success" active={true}>Active Success</Button>
			<Button color="error" disabled={true}>Disabled Error</Button>
		</div>
	</section>

	<!-- Shapes Section -->
	<section>
		<h2 class="mb-6 text-2xl font-semibold">Shapes & Variants</h2>
		<div class="flex flex-wrap items-center gap-4">
			<Button>Normal</Button>
			<Button wide={true}>Wide Button</Button>
			<Button square={true}>SQ</Button>
			<Button circle={true}>C</Button>
			<Button block={true}>Block Button (Full Width)</Button>
		</div>
	</section>

	<!-- With Links -->
	<section>
		<h2 class="mb-6 text-2xl font-semibold">Button as Link</h2>
		<div class="flex flex-wrap gap-4">
			<Button href="/">Link Button</Button>
			<Button href="/" color="secondary">Secondary Link</Button>
			<Button href="/" style="outline">Outline Link</Button>
			<Button href="/" style="link" color="info">Styled as Link</Button>
		</div>
	</section>

	<!-- Size Variations per Color -->
	<section>
		<h2 class="mb-6 text-2xl font-semibold">Size Variations</h2>
		<div class="space-y-6">
			<div class="space-y-3">
				<h3 class="text-sm font-medium text-gray-600">Primary Sizes</h3>
				<div class="flex flex-wrap items-center gap-3">
					<Button color="primary" size="xs">XS</Button>
					<Button color="primary" size="sm">SM</Button>
					<Button color="primary" size="md">MD</Button>
					<Button color="primary" size="lg">LG</Button>
					<Button color="primary" size="xl">XL</Button>
				</div>
			</div>
			<div class="space-y-3">
				<h3 class="text-sm font-medium text-gray-600">Outline Sizes</h3>
				<div class="flex flex-wrap items-center gap-3">
					<Button style="outline" size="xs">XS</Button>
					<Button style="outline" size="sm">SM</Button>
					<Button style="outline" size="md">MD</Button>
					<Button style="outline" size="lg">LG</Button>
					<Button style="outline" size="xl">XL</Button>
				</div>
			</div>
		</div>
	</section>

	<!-- Interactive Examples -->
	<section>
		<h2 class="mb-6 text-2xl font-semibold">Interactive Examples</h2>
		<div class="flex flex-wrap gap-4">
			<Button onclick={() => alert('Primary clicked!')}>Click Me</Button>
			<Button color="success" onclick={() => alert('Success!')}>Submit</Button>
			<Button color="error" onclick={() => alert('Cancelled')}>Cancel</Button>
			<Button color="info" style="outline" onclick={() => console.log('Info logged')}>
				Log Info
			</Button>
		</div>
	</section>
</div>
