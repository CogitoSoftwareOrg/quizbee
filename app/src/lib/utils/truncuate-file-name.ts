function truncateFileName(filename: string, maxLength: number = 50): string {
	if (filename.length <= maxLength) {
		return filename;
	}
	return filename.substring(0, maxLength - 3) + '...';
}

export { truncateFileName };
