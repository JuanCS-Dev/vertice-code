/**
 * Unit tests for Chat Store
 *
 * Testing framework: Vitest
 * Reference: https://vitest.dev/
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '@/lib/stores/chat-store';

describe('useChatStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useChatStore.setState({
      sessions: [],
      currentSessionId: null,
      messages: [],
      isLoading: false,
      error: null,
    });
  });

  it('adds a message', () => {
    const { addMessage, messages } = useChatStore.getState();

    addMessage({
      role: 'user',
      content: 'Hello',
    });

    expect(messages).toHaveLength(1);
    expect(messages[0].content).toBe('Hello');
    expect(messages[0].id).toBeDefined();
  });

  it('updates a message', () => {
    const { addMessage, updateMessage, messages } = useChatStore.getState();

    addMessage({ role: 'assistant', content: 'Initial' });
    const messageId = messages[0].id;

    updateMessage(messageId, 'Updated');

    expect(messages[0].content).toBe('Updated');
  });

  it('clears messages', () => {
    const { addMessage, clearMessages, messages } = useChatStore.getState();

    addMessage({ role: 'user', content: 'Test' });
    clearMessages();

    expect(messages).toHaveLength(0);
  });

  it('creates a new session', () => {
    const { createSession, sessions, currentSessionId } = useChatStore.getState();

    createSession();

    expect(sessions).toHaveLength(1);
    expect(currentSessionId).toBeDefined();
    expect(sessions[0].id).toBe(currentSessionId);
  });

  it('sets current session', () => {
    const { createSession, setCurrentSession, currentSessionId } = useChatStore.getState();

    createSession();
    const newSessionId = 'test-session-id';

    setCurrentSession(newSessionId);

    expect(currentSessionId).toBe(newSessionId);
  });

  it('deletes a session', () => {
    const { createSession, deleteSession, sessions } = useChatStore.getState();

    createSession();
    const sessionId = sessions[0].id;

    deleteSession(sessionId);

    expect(sessions).toHaveLength(0);
  });
});