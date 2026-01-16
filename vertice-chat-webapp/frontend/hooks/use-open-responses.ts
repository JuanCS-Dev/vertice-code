/**
 * React Hook for Open Responses Protocol
 *
 * Alternative to useChat from @ai-sdk/react for Open Responses protocol
 */

import { useState, useCallback, useRef } from 'react';
import { OpenResponsesClient, OpenResponsesMessage } from '@/lib/realtime/openresponses-client';

export interface UseOpenResponsesOptions {
  apiUrl?: string;
  onError?: (error: Error) => void;
  onFinish?: (usage?: any) => void;
}

export interface UseOpenResponsesReturn {
  messages: OpenResponsesMessage[];
  isLoading: boolean;
  error: Error | null;
  sendMessage: (content: string) => Promise<void>;
  stop: () => void;
}

export function useOpenResponses({
  apiUrl = '/api/chat',
  onError,
  onFinish,
}: UseOpenResponsesOptions = {}): UseOpenResponsesReturn {
  const [messages, setMessages] = useState<OpenResponsesMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');

  const clientRef = useRef<OpenResponsesClient | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    // Input validation
    if (!content || typeof content !== 'string') {
      const error = new Error('Message content must be a non-empty string');
      setError(error);
      onError?.(error);
      return;
    }

    if (content.length > 10000) { // Reasonable limit
      const error = new Error('Message content too long (max 10000 characters)');
      setError(error);
      onError?.(error);
      return;
    }

    if (isLoading) {
      console.warn('Attempted to send message while already loading');
      return;
    }

    setIsLoading(true);
    setError(null);
    setConnectionStatus('connecting');

    try {
      // Validate and add user message
      const userMessage: OpenResponsesMessage = {
        id: `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        role: 'user',
        content: content.trim(),
        timestamp: new Date(),
      };

      const currentMessages = [...messages, userMessage];
      setMessages(currentMessages);

      // Add assistant message placeholder with unique ID
      const assistantMessage: OpenResponsesMessage = {
        id: `assistant-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Get auth token with fallback
      const authToken = localStorage.getItem('authToken') ||
                       localStorage.getItem('firebaseToken') ||
                       'dev-token';

      if (!authToken || authToken === 'dev-token') {
        console.warn('Using development token - authentication may not work in production');
      }

      clientRef.current = new OpenResponsesClient(apiUrl, authToken);
      setConnectionStatus('connected');

      await clientRef.current.sendMessage(
        currentMessages.map(m => {
          // Validate message structure
          if (!m.role || !m.content) {
            console.warn('Invalid message structure:', m);
            return { role: m.role || 'user', content: m.content || '' };
          }
          return { role: m.role, content: m.content };
        }),
        {
          onMessage: (message) => {
            // Validate incoming message
            if (!message || typeof message.content !== 'string') {
              console.warn('Invalid message received:', message);
              return;
            }

            setMessages(prev =>
              prev.map(m =>
                m.id === assistantMessage.id
                  ? { ...m, content: message.content }
                  : m
              )
            );
          },
          onError: (err) => {
            console.error('Open Responses error:', err);
            setError(err);
            setIsLoading(false);
            setConnectionStatus('error');
            onError?.(err);
          },
          onComplete: (usage) => {
            console.log('Open Responses completed with usage:', usage);
            setIsLoading(false);
            setConnectionStatus('disconnected');
            onFinish?.(usage);
          },
        }
      );
    } catch (setupError) {
      console.error('Failed to setup Open Responses client:', setupError);
      const error = setupError instanceof Error ? setupError : new Error('Failed to initialize chat');
      setError(error);
      setIsLoading(false);
      setConnectionStatus('error');
      onError?.(error);
    }
  }, [messages, isLoading, apiUrl, onError, onFinish]);

  const stop = useCallback(() => {
    clientRef.current?.stop();
    setIsLoading(false);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    stop,
  };
}