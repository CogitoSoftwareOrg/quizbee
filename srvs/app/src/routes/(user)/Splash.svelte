<div
	class="bg-linear-to-br from-base-100 via-base-200 to-base-100 flex h-screen items-center justify-center"
>
	<div class="w-full max-w-md px-6">
		<!-- Animated Logo/Icon -->
		<div class="mb-10 flex justify-center">
			<div class="relative h-32 w-32">
				<!-- Outer rotating ring with gradient -->
				<div
					class="border-t-primary border-r-warning absolute inset-0 animate-spin rounded-full border-4 border-transparent opacity-80"
					style="animation-duration: 2s;"
				></div>
				<!-- Middle pulsing ring -->
				<div
					class="border-3 border-primary/20 absolute inset-3 animate-pulse rounded-full"
					style="animation-duration: 1.5s;"
				></div>
				<!-- Inner rotating reverse -->
				<div
					class="border-l-secondary border-b-accent absolute inset-6 animate-spin rounded-full border-2 border-transparent opacity-60"
					style="animation-duration: 3s; animation-direction: reverse;"
				></div>
				<!-- Center icon with bounce -->
				<div class="absolute inset-0 flex items-center justify-center">
					<div
						class="bg-linear-to-br from-primary/20 to-secondary/20 flex h-20 w-20 animate-bounce items-center justify-center rounded-full backdrop-blur-sm"
						style="animation-duration: 2s;"
					>
						<span class="text-5xl">🐝</span>
					</div>
				</div>
			</div>
		</div>

		<!-- Animated Title -->
		<div class="mb-8 text-center">
			<h2 class="text-base-content mb-3 text-3xl font-bold tracking-tight">
				<span class="inline-block animate-pulse">Welcome to QuizBee</span>
			</h2>
			<p class="text-base-content/70 text-lg">
				Setting up your learning space
				<span class="inline-flex gap-1">
					<span class="animate-bounce" style="animation-delay: 0s;">.</span>
					<span class="animate-bounce" style="animation-delay: 0.2s;">.</span>
					<span class="animate-bounce" style="animation-delay: 0.4s;">.</span>
				</span>
			</p>
		</div>

		<!-- Progress Steps -->
		<div class="hidden space-y-5 sm:block">
			<!-- Step 1 -->
			<div class="flex items-center gap-4">
				<div
					class="bg-success/20 flex h-12 w-12 shrink-0 items-center justify-center rounded-full backdrop-blur-sm"
				>
					<span class="text-2xl">✓</span>
				</div>
				<div class="flex-1">
					<div class="bg-base-300 h-2 w-full overflow-hidden rounded-full">
						<div
							class="bg-linear-to-r from-success to-success/80 h-full w-full animate-pulse"
						></div>
					</div>
					<p class="text-base-content mt-2 text-sm font-medium">Authenticating</p>
				</div>
			</div>

			<!-- Step 2 -->
			<div class="flex items-center gap-4">
				<div
					class="bg-primary/20 flex h-12 w-12 shrink-0 animate-pulse items-center justify-center rounded-full backdrop-blur-sm"
				>
					<span class="text-2xl">⚡</span>
				</div>
				<div class="flex-1">
					<div class="bg-base-300 h-2 w-full overflow-hidden rounded-full">
						<div
							class="bg-linear-to-r from-primary to-primary/80 h-full w-3/4 animate-pulse"
							style="animation-duration: 1s;"
						></div>
					</div>
					<p class="text-base-content mt-2 text-sm font-medium">Loading your data</p>
				</div>
			</div>

			<!-- Step 3 -->
			<div class="flex items-center gap-4 opacity-60">
				<div
					class="border-base-300 flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-2 border-dashed"
				>
					<span class="text-2xl">🎯</span>
				</div>
				<div class="flex-1">
					<div class="bg-base-300 h-2 w-full overflow-hidden rounded-full">
						<div class="bg-linear-to-r from-accent/50 h-full w-1/3 to-transparent"></div>
					</div>
					<p class="text-base-content mt-2 text-sm font-medium">Almost ready</p>
				</div>
			</div>
		</div>

		<!-- Fun fact card -->
		<div
			class="bg-linear-to-br from-primary/5 to-secondary/5 mt-10 animate-pulse rounded-2xl p-5 backdrop-blur-sm"
			style="animation-duration: 3s;"
		>
			<div class="flex items-start gap-3">
				<span class="text-3xl">💡</span>
				<div>
					<p class="text-base-content mb-1 text-sm font-semibold">Did you know?</p>
					<p class="text-base-content/70 text-xs">
						QuizBee uses AI to create personalized quizzes that adapt to your learning style!
					</p>
				</div>
			</div>
		</div>

		<!-- Animated wave dots -->
		<div class="mt-8 flex justify-center gap-2">
			<div
				class="bg-primary shadow-primary/50 h-3 w-3 animate-bounce rounded-full shadow-lg"
				style="animation-delay: 0s; animation-duration: 1s;"
			></div>
			<div
				class="bg-secondary shadow-secondary/50 h-3 w-3 animate-bounce rounded-full shadow-lg"
				style="animation-delay: 0.15s; animation-duration: 1s;"
			></div>
			<div
				class="bg-accent shadow-accent/50 h-3 w-3 animate-bounce rounded-full shadow-lg"
				style="animation-delay: 0.3s; animation-duration: 1s;"
			></div>
			<div
				class="bg-warning shadow-warning/50 h-3 w-3 animate-bounce rounded-full shadow-lg"
				style="animation-delay: 0.45s; animation-duration: 1s;"
			></div>
		</div>
	</div>
</div>
