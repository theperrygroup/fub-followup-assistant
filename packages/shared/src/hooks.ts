/**
 * React hooks for FUB Follow-up Assistant.
 * 
 * This file contains custom React hooks for managing authentication,
 * chat state, and other application state.
 */

import { useCallback, useEffect, useState } from 'react';
import {
  checkAuth,
  clearAuthToken,
  createNote,
  iframeLogin,
  sendChatMessage,
  setAuthToken,
} from './api';
import type {
  AuthState,
  ChatMessage,
  ChatRequest,
  ChatState,
  CreateNoteRequest,
  FubContext,
  IframeLoginRequest,
  SubscriptionStatus,
} from './types';

/**
 * Hook for managing authentication state.
 * 
 * @returns Authentication state and actions.
 */
export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    token: null,
    account: null,
  });

  /**
   * Authenticate with iframe context and signature.
   * 
   * @param context - Follow Up Boss context data.
   * @param signature - HMAC signature.
   * @returns Promise resolving to success status.
   */
  const login = useCallback(async (context: string, signature: string): Promise<boolean> => {
    setAuthState(prev => ({ ...prev, isLoading: true }));

    const request: IframeLoginRequest = { context, signature };
    const result = await iframeLogin(request);

    if (result.error) {
      setAuthState(prev => ({
        ...prev,
        isLoading: false,
        isAuthenticated: false,
      }));
      return false;
    }

    const { token, account_id, fub_account_id, subscription_status } = result.data;
    
    setAuthToken(token);
    
    setAuthState({
      isAuthenticated: true,
      isLoading: false,
      token,
      account: {
        account_id,
        fub_account_id,
        subscription_status: subscription_status as SubscriptionStatus,
      },
    });

    return true;
  }, []);

  /**
   * Log out the user.
   */
  const logout = useCallback(() => {
    clearAuthToken();
    setAuthState({
      isAuthenticated: false,
      isLoading: false,
      token: null,
      account: null,
    });
  }, []);

  /**
   * Check authentication status on mount.
   */
  useEffect(() => {
    checkAuth().then(isAuthenticated => {
      setAuthState(prev => ({
        ...prev,
        isAuthenticated,
        isLoading: false,
      }));
    });
  }, []);

  return {
    ...authState,
    login,
    logout,
  };
}

/**
 * Hook for managing chat state and actions.
 * 
 * @returns Chat state and actions.
 */
export function useChat() {
  const [chatState, setChatState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
    currentPersonId: null,
  });

  /**
   * Send a chat message and get AI response.
   * 
   * @param question - The user's question.
   * @param personId - Follow Up Boss person ID.
   * @returns Promise resolving to success status.
   */
  const sendMessage = useCallback(async (question: string, personId: string): Promise<boolean> => {
    if (!question.trim()) return false;

    setChatState(prev => ({
      ...prev,
      isLoading: true,
      error: null,
      currentPersonId: personId,
    }));

    // Add user message to chat
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      content: question,
      role: 'user',
      timestamp: new Date(),
      person_id: personId,
    };

    setChatState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
    }));

    // Send request to API
    const request: ChatRequest = {
      person_id: personId,
      question,
    };

    const result = await sendChatMessage(request);

    if (result.error) {
      setChatState(prev => ({
        ...prev,
        isLoading: false,
        error: result.error?.detail || 'Failed to send message',
      }));
      return false;
    }

    // Add AI response to chat
    const aiMessage: ChatMessage = {
      id: `assistant-${Date.now()}`,
      content: result.data.answer,
      role: 'assistant',
      timestamp: new Date(),
      person_id: personId,
    };

    setChatState(prev => ({
      ...prev,
      messages: [...prev.messages, aiMessage],
      isLoading: false,
    }));

    return true;
  }, []);

  /**
   * Clear chat history.
   */
  const clearMessages = useCallback(() => {
    setChatState(prev => ({
      ...prev,
      messages: [],
      error: null,
    }));
  }, []);

  /**
   * Set error state.
   * 
   * @param error - Error message.
   */
  const setError = useCallback((error: string | null) => {
    setChatState(prev => ({ ...prev, error }));
  }, []);

  return {
    ...chatState,
    sendMessage,
    clearMessages,
    setError,
  };
}

/**
 * Hook for creating notes in Follow Up Boss.
 * 
 * @returns Note creation function and state.
 */
export function useCreateNote() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Create a note in Follow Up Boss.
   * 
   * @param content - Note content.
   * @param personId - Follow Up Boss person ID.
   * @returns Promise resolving to success status.
   */
  const createFubNote = useCallback(async (content: string, personId: string): Promise<boolean> => {
    if (!content.trim()) return false;

    setIsLoading(true);
    setError(null);

    const request: CreateNoteRequest = {
      content,
      person_id: personId,
    };

    const result = await createNote(request);

    setIsLoading(false);

    if (result.error) {
      setError(result.error.detail);
      return false;
    }

    return true;
  }, []);

  return {
    createNote: createFubNote,
    isLoading,
    error,
    setError,
  };
}

/**
 * Hook for parsing Follow Up Boss context from URL parameters.
 * 
 * @returns Context data and signature if available.
 */
export function useFubContext() {
  const [context, setContext] = useState<FubContext | null>(null);
  const [signature, setSignature] = useState<string | null>(null);
  const [contextString, setContextString] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const urlParams = new URLSearchParams(window.location.search);
    const contextParam = urlParams.get('context');
    const signatureParam = urlParams.get('signature');

    if (contextParam && signatureParam) {
      try {
        const parsedContext = JSON.parse(decodeURIComponent(contextParam));
        setContext(parsedContext);
        setSignature(signatureParam);
        setContextString(contextParam);
      } catch (error) {
        console.error('Failed to parse FUB context:', error);
      }
    }
  }, []);

  return {
    context,
    signature,
    contextString,
  };
} 