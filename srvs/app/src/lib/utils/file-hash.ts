import { blake3 } from '@noble/hashes/blake3.js';

export async function computeFileHash(file: File): Promise<string> {
	const buffer = await file.arrayBuffer();
	const hash = blake3(new Uint8Array(buffer));
	return Array.from(hash)
		.map((b) => b.toString(16).padStart(2, '0'))
		.join('');
}
