/**
 * Shared TypeScript types for FUB Follow-up Assistant.
 * 
 * This file contains all the common types used across the frontend
 * applications including API request/response models and enums.
 */

/** Subscription status enumeration. */
export enum SubscriptionStatus {
  ACTIVE = "active",
  CANCELLED = "cancelled",
  INCOMPLETE = "incomplete",
  PAST_DUE = "past_due",
  TRIALING = "trialing",
  UNPAID = "unpaid",
}

/** API Authentication types. */
export interface IframeLoginRequest {
  /** Context data from Follow Up Boss iframe. */
  context: string;
  /** HMAC signature for verification. */
  signature: string;
}

export interface IframeLoginResponse {
  /** Internal account ID. */
  account_id: number;
  /** Follow Up Boss account ID. */
  fub_account_id: string;
  /** Current subscription status. */
  subscription_status: string;
  /** JWT authentication token. */
  token: string;
}

export interface TokenRefreshResponse {
  /** New JWT token. */
  token: string;
}

/** Chat API types. */
export interface ChatRequest {
  /** Follow Up Boss person ID. */
  person_id: string;
  /** User's question about the lead. */
  question: string;
}

export interface ChatResponse {
  /** AI-generated follow-up advice. */
  answer: string;
  /** Follow Up Boss person ID. */
  person_id: string;
}

/** FUB API types. */
export interface CreateNoteRequest {
  /** Note content to create. */
  content: string;
  /** Follow Up Boss person ID. */
  person_id: string;
}

export interface CreateNoteResponse {
  /** ID of the created note. */
  note_id: string;
  /** Follow Up Boss person ID. */
  person_id: string;
  /** Success status. */
  success: boolean;
}

/** Chat message types for UI. */
export interface ChatMessage {
  /** Unique message ID. */
  id: string;
  /** Message content. */
  content: string;
  /** Message role (user or assistant). */
  role: "user" | "assistant";
  /** Message timestamp. */
  timestamp: Date;
  /** Follow Up Boss person ID this message relates to. */
  person_id?: string;
}

/** Application state types. */
export interface AuthState {
  /** Whether user is authenticated. */
  isAuthenticated: boolean;
  /** Whether authentication is being checked. */
  isLoading: boolean;
  /** JWT token. */
  token: string | null;
  /** Account information. */
  account: {
    account_id: number;
    fub_account_id: string;
    subscription_status: SubscriptionStatus;
  } | null;
}

export interface ChatState {
  /** Chat messages. */
  messages: ChatMessage[];
  /** Whether a request is in progress. */
  isLoading: boolean;
  /** Error message if any. */
  error: string | null;
  /** Current person ID being discussed. */
  currentPersonId: string | null;
}

/** Error types. */
export interface ApiError {
  /** Error message. */
  detail: string;
  /** Error code if available. */
  error_code?: string;
  /** Additional error information. */
  error_id?: string;
}

/** Utility types. */
export type ApiResponse<T> = {
  data: T;
  error: null;
} | {
  data: null;
  error: ApiError;
};

/** Follow Up Boss context data structure. */
export interface FubContext {
  /** Account information. */
  account: {
    /** Account ID. */
    id: string;
    /** Account name. */
    name: string;
  };
  /** User information. */
  user: {
    /** User ID. */
    id: string;
    /** User name. */
    name: string;
    /** User email. */
    email: string;
  };
  /** Current person being viewed (if any). */
  person?: {
    /** Person ID. */
    id: string;
    /** Person name. */
    name: string;
    /** Person email. */
    email?: string;
    /** Person phone. */
    phone?: string;
  };
}

/** Stripe checkout session data. */
export interface StripeCheckoutSession {
  /** Checkout session ID. */
  id: string;
  /** Checkout session URL. */
  url: string;
}

/** Stripe customer portal session data. */
export interface StripeCustomerPortalSession {
  /** Portal session URL. */
  url: string;
} 