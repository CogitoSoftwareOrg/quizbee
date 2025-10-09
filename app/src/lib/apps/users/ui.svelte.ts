import { Preferences } from '@capacitor/preferences';
import { z } from 'zod';

const UIStateSchema = z.object({
	paywallOpen: z.boolean().default(false),
	globalSidebarOpen: z.boolean().default(true)
});

type UIState = z.infer<typeof UIStateSchema>;

class UIStore {
	private _state: UIState | null = $state(UIStateSchema.parse({}));

	paywallOpen = $derived(this._state?.paywallOpen);
	globalSidebarOpen = $derived(this._state?.globalSidebarOpen);

	// paywallOpen
	togglePaywallOpen() {
		if (!this._state) return;
		this._state.paywallOpen = !this._state.paywallOpen;
		this.saveState();
	}
	setPaywallOpen(open: boolean) {
		if (!this._state) return;
		this._state.paywallOpen = open;
		this.saveState();
	}

	// globalSidebarOpen
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
			try {
				this._state = UIStateSchema.parse(JSON.parse(raw.value));
				return;
			} catch {
				console.error('Failed to parse UI state');
			}
		}

		this._state = UIStateSchema.parse({});
		await this.saveState();
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
