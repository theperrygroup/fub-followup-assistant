import { useEffect, useState } from 'react'
import type { FubContext } from '@fub-assistant/shared'

interface AuthScreenProps {
  onLogin: (context: string, signature: string) => Promise<void>
  context: FubContext | null
}

export function AuthScreen({ onLogin, context }: AuthScreenProps) {
  const [isAuthenticating, setIsAuthenticating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const handleIframeAuth = async () => {
      try {
        setIsAuthenticating(true)
        setError(null)

        // Get iframe parameters from URL or FUB context
        const urlParams = new URLSearchParams(window.location.search)
        const contextParam = urlParams.get('context')
        const signatureParam = urlParams.get('signature')

        if (contextParam && signatureParam) {
          await onLogin(contextParam, signatureParam)
        } else {
          // Try to get from parent window (FUB iframe)
          const message = {
            type: 'fub_auth_request',
            timestamp: Date.now()
          }
          window.parent.postMessage(message, '*')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Authentication failed')
      } finally {
        setIsAuthenticating(false)
      }
    }

    // Listen for auth data from parent
    const handleMessage = async (event: MessageEvent) => {
      if (event.data.type === 'fub_auth_data') {
        try {
          setIsAuthenticating(true)
          setError(null)
          await onLogin(event.data.context, event.data.signature)
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Authentication failed')
        } finally {
          setIsAuthenticating(false)
        }
      }
    }

    window.addEventListener('message', handleMessage)
    handleIframeAuth()

    return () => {
      window.removeEventListener('message', handleMessage)
    }
  }, [onLogin])

  return (
    <div className="flex items-center justify-center h-full bg-gradient-to-br from-blue-50 to-white p-6">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
        <div className="mb-6">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">
            FUB Follow-up Assistant
          </h1>
          <p className="text-gray-600">
            AI-powered follow-up assistance for your leads
          </p>
        </div>

        {isAuthenticating ? (
          <div className="space-y-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-sm text-gray-500">Authenticating with Follow Up Boss...</p>
          </div>
        ) : error ? (
          <div className="space-y-3">
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
            >
              Try Again
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-gray-500">
              Connecting to Follow Up Boss...
            </p>
            {context && (
              <div className="text-xs text-gray-400 border-t pt-3">
                <p>Account: {context.account?.name}</p>
                <p>User: {context.user?.name}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
} 