// это тип для прикрепленного файла при создании нового квиза
type AttachedFile = {
	file?: File;
	previewUrl: string | null;
	materialId: string;
	name: string;
	isUploading?: boolean;
	isIndexing?: boolean;
	isHashing?: boolean;
	tokens?: number;
	isBook?: boolean;
	textFile?: File;
	hash?: string;
};

export type { AttachedFile };
