export function debounce<T extends (...args: unknown[]) => void>(fn: T, delay: number) {
	let timeout: ReturnType<typeof setTimeout>;
	return (...args: Parameters<T>) => {
		clearTimeout(timeout);
		timeout = setTimeout(() => {
			fn(...args);
		}, delay);
	};
}
