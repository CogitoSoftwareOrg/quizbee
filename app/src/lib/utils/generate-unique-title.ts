function generateUniqueTitle(baseTitle: string, existingTitles: string[]): string {
	let title = baseTitle;
	let counter = 1;
	while (existingTitles.includes(title)) {
		title = `${baseTitle} (${counter})`;
		counter++;
	}
	return title;
}

export { generateUniqueTitle };
