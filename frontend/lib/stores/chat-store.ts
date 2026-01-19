import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';

export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;

  // Actions
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  error: null,

  addMessage: (msg) => {
    set((state) => ({
      messages: [
        ...state.messages,
        {
          id: uuidv4(),
          timestamp: new Date(),
          ...msg,
        },
      ],
    }));
  },

  sendMessage: async (content: string) => {
    const { addMessage } = get();

    // 1. Add User Message
    addMessage({ role: 'user', content });

    // 2. Prepare Assistant Message Placeholder
    const assistantMsgId = uuidv4();
    set((state) => ({
      isLoading: true,
      error: null,
      messages: [
        ...state.messages,
        {
          id: assistantMsgId,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          isStreaming: true,
        },
      ],
    }));

    try {
      // 3. Connect to SSE Endpoint
      const response = await fetch(`${API_URL}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // 'Authorization': `Bearer ${token}` // TODO: Add Auth
        },
        body: JSON.stringify({
          messages: get().messages.map(m => ({
            role: m.role,
            content: m.content
          })).filter(m => m.id !== assistantMsgId), // Don't send the empty placeholder
          stream: true
        }),
      });

      if (!response.ok) throw new Error('Failed to connect to chat stream');
      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      // 4. Read the Stream
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6);
            if (dataStr === '[DONE]') continue;

            try {
              const event = JSON.parse(dataStr);

              // Handle "token" event
              if (event.type === 'token') {
                const token = event.data?.token || '';

                // Update specific message content efficiently
                set((state) => ({
                  messages: state.messages.map((msg) =>
                    msg.id === assistantMsgId
                      ? { ...msg, content: msg.content + token }
                      : msg
                  ),
                }));
              }

              // Handle "error" event
              if (event.type === 'error') {
                 console.error('Stream error:', event.data);
              }

            } catch (e) {
              // Ignore parse errors for keep-alive or ping
            }
          }
        }
      }

    } catch (error) {
      console.error('Chat error:', error);
      set({ error: (error as Error).message });
    } finally {
      // 5. Finish Streaming
      set((state) => ({
        isLoading: false,
        messages: state.messages.map((msg) =>
          msg.id === assistantMsgId
            ? { ...msg, isStreaming: false }
            : msg
        ),
      }));
    }
  },

  clearMessages: () => set({ messages: [] }),
}));
