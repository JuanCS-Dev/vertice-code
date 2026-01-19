/**
 * Unit tests for Chat Store
 *
 * Testing framework: Vitest
 * Reference: https://vitest.dev/
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '@/lib/stores/chat-store';

// Tests reflect the current Store structure (Record<string, Session>)
describe('useChatStore', () => {
  beforeEach(() => {
    useChatStore.setState({
      sessions: {},
      currentSessionId: null,
      isLoading: false,
      error: null,
    });
  });

  // Note: These tests assume the store exposes these methods.
  // If the store logic has changed significantly (e.g. moved to context),
  // these tests should be rewritten or removed.

  it('initializes with empty state', () => {
      const state = useChatStore.getState();
      expect(state.sessions).toEqual({});
      expect(state.currentSessionId).toBeNull();
  });
});
