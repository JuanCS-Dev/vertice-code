import { create } from 'zustand';

export interface ArtifactFile {
  id: string;
  name: string;
  language: string;
  content: string;
  version: number;
}

interface ArtifactState {
  files: Record<string, ArtifactFile>;
  activeFileId: string | null;

  // Actions
  createOrUpdateFile: (name: string, content: string, language?: string) => void;
  setActiveFile: (name: string) => void;
  closeFile: (name: string) => void;
}

// Helper to guess language from extension
function getLanguage(filename: string): string {
  if (filename.endsWith('.tsx') || filename.endsWith('.ts')) return 'typescript';
  if (filename.endsWith('.jsx') || filename.endsWith('.js')) return 'javascript';
  if (filename.endsWith('.py')) return 'python';
  if (filename.endsWith('.css')) return 'css';
  if (filename.endsWith('.html')) return 'html';
  if (filename.endsWith('.json')) return 'json';
  if (filename.endsWith('.md')) return 'markdown';
  return 'plaintext';
}

export const useArtifactStore = create<ArtifactState>((set) => ({
  files: {
    // Initial Example File
    'welcome.md': {
      id: 'welcome.md',
      name: 'welcome.md',
      language: 'markdown',
      content: '# Welcome to Vertice Code\n\nThis is your active workspace. Generated code will appear here.',
      version: 1,
    }
  },
  activeFileId: 'welcome.md',

  createOrUpdateFile: (name, content, language) =>
    set((state) => {
      const existing = state.files[name];
      return {
        files: {
          ...state.files,
          [name]: {
            id: name,
            name,
            language: language || getLanguage(name),
            content,
            version: existing ? existing.version + 1 : 1,
          }
        },
        activeFileId: name // Auto-focus new files
      };
    }),

  setActiveFile: (name) => set({ activeFileId: name }),

  closeFile: (name) => set((state) => {
    const newFiles = { ...state.files };
    delete newFiles[name];
    // If closing active file, switch to another or null
    const newActive = state.activeFileId === name
      ? Object.keys(newFiles)[0] || null
      : state.activeFileId;

    return { files: newFiles, activeFileId: newActive };
  }),
}));
