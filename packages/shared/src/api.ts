/**
 * API client utilities for FUB Follow-up Assistant.
 * 
 * This file contains functions for making HTTP requests to the backend API
 * with proper error handling and type safety.
 */

import type {
  ApiError,
  ApiResponse,
  ChatRequest,
  ChatResponse,
  CreateNoteRequest,
  CreateNoteResponse,
  IframeLoginRequest,
  IframeLoginResponse,
  TokenRefreshResponse,
} from './types';

/** Base API URL - will be set by the consuming application. */
let API_BASE_URL = '';

/**
 * Set the base URL for API requests.
 * 
 * @param url - The base URL for the API.
 */
export function setApiBaseUrl(url: string): void {
  API_BASE_URL = url.replace(/\/$/, ''); // Remove trailing slash
}

/**
 * Get the current JWT token from session storage.
 * 
 * @returns The JWT token or null if not found.
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return sessionStorage.getItem('fub_auth_token');
}

/**
 * Set the JWT token in session storage.
 * 
 * @param token - The JWT token to store.
 */
export function setAuthToken(token: string): void {
  if (typeof window === 'undefined') return;
  sessionStorage.setItem('fub_auth_token', token);
}

/**
 * Remove the JWT token from session storage.
 */
export function clearAuthToken(): void {
  if (typeof window === 'undefined') return;
  sessionStorage.removeItem('fub_auth_token');
}

/**
 * Make an HTTP request with proper error handling.
 * 
 * @param endpoint - The API endpoint path.
 * @param options - Fetch options.
 * @returns Promise resolving to the response data or error.
 */
async function makeRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = getAuthToken();
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };
    
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    
    const response = await fetch(url, {
      ...options,
      headers,
    });
    
    if (!response.ok) {
      let error: ApiError;
      try {
        error = await response.json();
      } catch {
        error = {
          detail: `HTTP ${response.status}: ${response.statusText}`,
        };
      }
      
      return { data: null, error };
    }
    
    const data = await response.json();
    return { data, error: null };
    
  } catch (err) {
    return {
      data: null,
      error: {
        detail: err instanceof Error ? err.message : 'Network error',
      },
    };
  }
}

/**
 * Authenticate iframe request and get JWT token.
 * 
 * @param request - The iframe login request.
 * @returns Promise resolving to the authentication response.
 */
export async function iframeLogin(
  request: IframeLoginRequest
): Promise<ApiResponse<IframeLoginResponse>> {
  return makeRequest<IframeLoginResponse>('/api/v1/auth/iframe-login', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Refresh JWT token.
 * 
 * @returns Promise resolving to the new token.
 */
export async function refreshToken(): Promise<ApiResponse<TokenRefreshResponse>> {
  return makeRequest<TokenRefreshResponse>('/api/v1/auth/refresh');
}

/**
 * Send a chat message and get AI response.
 * 
 * @param request - The chat request.
 * @returns Promise resolving to the chat response.
 */
export async function sendChatMessage(
  request: ChatRequest
): Promise<ApiResponse<ChatResponse>> {
  return makeRequest<ChatResponse>('/api/v1/chat', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Create a note in Follow Up Boss.
 * 
 * @param request - The note creation request.
 * @returns Promise resolving to the note creation response.
 */
export async function createNote(
  request: CreateNoteRequest
): Promise<ApiResponse<CreateNoteResponse>> {
  return makeRequest<CreateNoteResponse>('/api/v1/fub/note', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Check if the user is authenticated by verifying token validity.
 * 
 * @returns Promise resolving to true if authenticated, false otherwise.
 */
export async function checkAuth(): Promise<boolean> {
  const token = getAuthToken();
  if (!token) return false;
  
  // Try to refresh token to verify it's valid
  const result = await refreshToken();
  
  if (result.error) {
    clearAuthToken();
    return false;
  }
  
  if (result.data) {
    setAuthToken(result.data.token);
  }
  
  return true;
} 