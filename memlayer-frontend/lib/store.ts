import { create } from 'zustand';
import { Workspace, Chat, Memory } from '@/types';

interface AppStore {
  // Workspaces
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  
  // Chats
  chats: Chat[];
  currentChat: Chat | null;
  
  // Memories
  recentMemories: Memory[];
  
  // UI State
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setCurrentWorkspace: (workspace: Workspace | null) => void;
  setWorkspaces: (workspaces: Workspace[]) => void;
  setCurrentChat: (chat: Chat | null) => void;
  setChats: (chats: Chat[]) => void;
  setRecentMemories: (memories: Memory[]) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  workspaces: [],
  currentWorkspace: null,
  chats: [],
  currentChat: null,
  recentMemories: [],
  isLoading: false,
  error: null,
  
  setCurrentWorkspace: (workspace) => set({ currentWorkspace: workspace }),
  setWorkspaces: (workspaces) => set({ workspaces }),
  setCurrentChat: (chat) => set({ currentChat: chat }),
  setChats: (chats) => set({ chats }),
  setRecentMemories: (memories) => set({ recentMemories: memories }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));
