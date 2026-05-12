import { create } from 'zustand';

interface RuntimeState {
  isPolling: boolean;
  selectedWorkspace: string | null;
  togglePolling: () => void;
  selectWorkspace: (id: string | null) => void;
}

export const useRuntimeStore = create<RuntimeState>((set) => ({
  isPolling: true,
  selectedWorkspace: null,
  togglePolling: () => set((state) => ({ isPolling: !state.isPolling })),
  selectWorkspace: (id) => set({ selectedWorkspace: id }),
}));
