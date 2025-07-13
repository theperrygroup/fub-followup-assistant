import { useState, useEffect } from 'react'

interface LeadInfo {
  id: number
  firstName: string
  lastName: string
  email?: string
  phone?: string
  stage: string
}

interface AuthState {
  isLoading: boolean
  isAuthenticated: boolean
  error?: string
  leadInfo?: LeadInfo
  token?: string
}

function App() {
  const [authState, setAuthState] = useState<AuthState>({
    isLoading: true,
    isAuthenticated: false
  })
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<Array<{role: 'user' | 'assistant', content: string}>>([])
  const [isTyping, setIsTyping] = useState(false)

  useEffect(() => {
    console.log('App starting - checking URL parameters...')
    console.log('Current URL:', window.location.href)
    console.log('Search params:', window.location.search)
    
    // Parse URL parameters
    const urlParams = new URLSearchParams(window.location.search)
    const context = urlParams.get('context')
    const signature = urlParams.get('signature')

    console.log('URL params found:', { 
      hasContext: !!context, 
      hasSignature: !!signature,
      contextLength: context?.length || 0,
      signatureLength: signature?.length || 0
    })

    if (!context || !signature) {
      console.warn('Missing authentication parameters')
      setAuthState({
        isLoading: false,
        isAuthenticated: false,
        error: 'Missing authentication parameters (context or signature not found in URL)'
      })
      return
    }

    // Authenticate with backend
    authenticateWithBackend(context, signature)
  }, [])

  const authenticateWithBackend = async (context: string, signature: string) => {
    try {
      console.log('Starting authentication...')
      console.log('Context length:', context.length)
      console.log('Signature length:', signature.length)
      console.log('Context (first 100 chars):', context.substring(0, 100))
      console.log('Signature:', signature)
      
      // Send the original base64 context for HMAC verification
      const response = await fetch('https://fub-followup-assistant-production.up.railway.app/auth/callback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ context, signature })
      })

      console.log('Response status:', response.status)
      console.log('Response headers:', Object.fromEntries(response.headers.entries()))

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Authentication failed - Response text:', errorText)
        
        let errorData: any = {}
        try {
          errorData = JSON.parse(errorText)
        } catch (e) {
          console.error('Could not parse error response as JSON')
        }
        
        throw new Error(errorData.detail || errorText || 'Authentication failed')
      }

      const data = await response.json()
      console.log('Authentication successful:', data)
      
      // Decode the base64 context locally to get lead info
      const decodedContext = atob(context)
      const contextData = JSON.parse(decodedContext)
      console.log('Decoded context data:', contextData)
      
      const person = contextData.person

      setAuthState({
        isLoading: false,
        isAuthenticated: true,
        token: data.token,
        leadInfo: {
          id: person.id,
          firstName: person.firstName,
          lastName: person.lastName,
          email: person.emails?.[0]?.value,
          phone: person.phones?.[0]?.value,
          stage: person.stage?.name || 'Unknown'
        }
      })

      // Add welcome message
      setMessages([{
        role: 'assistant',
        content: `Hi! I'm your FUB Follow-up Assistant. I can help you craft personalized follow-up messages for ${person.firstName} ${person.lastName}. What would you like help with?`
      }])

    } catch (error) {
      console.error('Authentication error:', error)
      setAuthState({
        isLoading: false,
        isAuthenticated: false,
        error: error instanceof Error ? error.message : 'Failed to authenticate with FUB'
      })
    }
  }

  const sendMessage = async () => {
    if (!message.trim() || !authState.token) return

    const userMessage = message.trim()
    setMessage('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setIsTyping(true)

    try {
      const response = await fetch('https://fub-followup-assistant-production.up.railway.app/api/v1/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authState.token}`
        },
        body: JSON.stringify({
          message: userMessage,
          lead_context: authState.leadInfo
        })
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const data = await response.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }])
    } finally {
      setIsTyping(false)
    }
  }

  if (authState.isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-50 to-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-lg font-semibold text-gray-700 mb-2">FUB Follow-up Assistant</h2>
          <p className="text-sm text-gray-500">Authenticating with FUB...</p>
        </div>
      </div>
    )
  }

  if (!authState.isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-red-50 to-white">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-gray-700 mb-2">Authentication Error</h2>
          <p className="text-sm text-gray-500">{authState.error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header */}
      <div className="bg-blue-600 text-white p-4 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <div>
            <h1 className="font-semibold">Follow-up Assistant</h1>
            <p className="text-sm text-blue-100">
              {authState.leadInfo?.firstName} {authState.leadInfo?.lastName} • {authState.leadInfo?.stage}
            </p>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-800'
              }`}
            >
              <p className="text-sm">{msg.content}</p>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Message Input */}
      <div className="border-t p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask for help with follow-up ideas..."
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={sendMessage}
            disabled={!message.trim() || isTyping}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

export default App 