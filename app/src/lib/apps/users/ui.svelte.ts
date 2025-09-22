import { Preferences } from '@capacitor/preferences';
import { z } from 'zod';

const UIStateSchema = z.object({
	globalSidebarOpen: z.boolean().default(true)
});

type UIState = z.infer<typeof UIStateSchema>;

class UIStore {
	private _state: UIState | null = $state(null);

	globalSidebarOpen = $derived(this._state?.globalSidebarOpen);

	toggleGlobalSidebar() {
		if (!this._state) return;
		this._state.globalSidebarOpen = !this._state.globalSidebarOpen;
		this.saveState();
	}
	setGlobalSidebarOpen(open: boolean) {
		if (!this._state) return;
		this._state.globalSidebarOpen = open;
		this.saveState();
	}

	async loadState() {
		console.log('loadState');
		const raw = await Preferences.get({ key: 'uiState' });
		if (raw.value) {
			const state = UIStateSchema.parse(JSON.parse(raw.value));
			this._state = state;
		}

		this._state = UIStateSchema.parse({});
	}

	private async saveState() {
		await Preferences.set({ key: 'uiState', value: JSON.stringify(this._state) });
	}

	clear() {
		this._state = UIStateSchema.parse({});
		this.saveState();
	}
}

export const uiStore = new UIStore();
