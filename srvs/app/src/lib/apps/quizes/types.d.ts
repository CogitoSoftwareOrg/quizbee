export type Answer = {
	content: string;
	correct: boolean;
	explanation: string;
};

export type UsedChunk = {
	id: string;
	materialId: string;
	title: string;
	page: number;
};
