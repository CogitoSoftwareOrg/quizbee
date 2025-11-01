export function clickOutside(
	node: HTMLElement,
	opts: { callback: () => void; ignore?: HTMLElement | HTMLElement[] | null }
) {
	const { callback, ignore } = opts;
	const handleClick = (event: MouseEvent) => {
		if (ignore) {
			if (Array.isArray(ignore)) {
				if (ignore.some((el) => el && el.contains(event.target as Node))) return;
			} else {
				if (ignore.contains(event.target as Node)) return;
			}
		}
		if (!node.contains(event.target as Node)) {
			callback();
		}
	};
	document.addEventListener('click', handleClick, true);
	return {
		destroy() {
			document.removeEventListener('click', handleClick, true);
		}
	};
}
