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
    console.log('=== APP INITIALIZATION START ===')
    console.log('App component mounted at:', new Date().toISOString())
    console.log('Current URL (full):', window.location.href)
    console.log('Current origin:', window.location.origin)
    console.log('Current pathname:', window.location.pathname)
    console.log('Current search:', window.location.search)
    console.log('Current hash:', window.location.hash)
    console.log('Document referrer:', document.referrer)
    console.log('User agent:', navigator.userAgent)
    
    // Check if we're in an iframe
    const isInIframe = window.self !== window.top
    console.log('Running in iframe:', isInIframe)
    
    if (isInIframe) {
      console.log('Iframe detected - this is good for FUB embedding')
      try {
        console.log('Parent origin:', window.parent.location.origin)
      } catch (e) {
        console.log('Cannot access parent origin (cross-origin):', e instanceof Error ? e.message : 'Unknown error')
      }
    } else {
      console.log('NOT in iframe - might be direct access or testing')
    }
    
    // Parse URL parameters with extensive logging
    const urlParams = new URLSearchParams(window.location.search)
    console.log('=== URL PARAMETER ANALYSIS ===')
    console.log('Raw search string:', window.location.search)
    console.log('URLSearchParams size:', urlParams.size)
    
    // Log all parameters
    console.log('All URL parameters:')
    for (const [key, value] of urlParams.entries()) {
      console.log(`  ${key}: ${value.substring(0, 50)}${value.length > 50 ? '...' : ''}`)
    }
    
    const context = urlParams.get('context')
    const signature = urlParams.get('signature')

    console.log('=== AUTHENTICATION PARAMETERS ===')
    console.log('Context found:', !!context)
    console.log('Signature found:', !!signature)
    
    if (context) {
      console.log('Context length:', context.length)
      console.log('Context (first 100 chars):', context.substring(0, 100))
      console.log('Context (last 50 chars):', context.substring(context.length - 50))
      
      // Try to decode context locally for debugging
      try {
        console.log('=== LOCAL CONTEXT DECODING TEST ===')
        let contextStr = context
        const originalLength = contextStr.length
        
        // Add padding if needed
        const padding = 4 - (contextStr.length % 4)
        if (padding !== 4) {
          contextStr += '='.repeat(padding)
          console.log(`Added ${padding} padding characters`)
        }
        
        console.log(`Context length: ${originalLength} -> ${contextStr.length}`)
        
        const decoded = atob(contextStr)
        console.log('Base64 decode successful, length:', decoded.length)
        console.log('Decoded context (first 200 chars):', decoded.substring(0, 200))
        
        const parsed = JSON.parse(decoded)
        console.log('JSON parse successful')
        console.log('Parsed context structure:', Object.keys(parsed))
        console.log('Account ID:', parsed.account?.id)
        console.log('Person:', parsed.person?.firstName, parsed.person?.lastName)
        console.log('Context type:', parsed.context)
      } catch (e) {
        console.error('Local context decoding failed:', e)
      }
    } else {
      console.warn('❌ NO CONTEXT PARAMETER FOUND')
    }
    
    if (signature) {
      console.log('Signature length:', signature.length)
      console.log('Signature:', signature)
    } else {
      console.warn('❌ NO SIGNATURE PARAMETER FOUND')
    }

    if (!context || !signature) {
      console.error('=== MISSING AUTHENTICATION PARAMETERS ===')
      console.error('This usually means:')
      console.error('1. FUB is not passing the parameters correctly')
      console.error('2. The iframe URL in FUB settings is wrong')
      console.error('3. This is a direct access (not through FUB)')
      
      setAuthState({
        isLoading: false,
        isAuthenticated: false,
        error: `Missing authentication parameters. Context: ${!!context}, Signature: ${!!signature}. URL: ${window.location.href}`
      })
      return
    }

    // Authenticate with backend
    console.log('=== STARTING BACKEND AUTHENTICATION ===')
    authenticateWithBackend(context, signature)
  }, [])

  const authenticateWithBackend = async (context: string, signature: string) => {
    console.log('=== BACKEND AUTHENTICATION START ===')
    console.log('Backend URL: https://fub-followup-assistant-production.up.railway.app/auth/callback')
    console.log('Context length:', context.length)
    console.log('Signature length:', signature.length)
    console.log('Context (first 100 chars):', context.substring(0, 100))
    console.log('Signature:', signature)
    
    const requestPayload = { context, signature }
    console.log('Request payload:', requestPayload)
    
    try {
      console.log('Making fetch request...')
      const startTime = Date.now()
      
      const response = await fetch('https://fub-followup-assistant-production.up.railway.app/auth/callback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestPayload)
      })

      const endTime = Date.now()
      console.log(`Request completed in ${endTime - startTime}ms`)
      console.log('=== RESPONSE DETAILS ===')
      console.log('Response status:', response.status)
      console.log('Response statusText:', response.statusText)
      console.log('Response ok:', response.ok)
      console.log('Response type:', response.type)
      console.log('Response url:', response.url)
      
      // Log all response headers
      console.log('Response headers:')
      for (const [key, value] of response.headers.entries()) {
        console.log(`  ${key}: ${value}`)
      }

      // Get response text first to handle both success and error cases
      const responseText = await response.text()
      console.log('Response body length:', responseText.length)
      console.log('Response body:', responseText)

      if (!response.ok) {
        console.error('=== AUTHENTICATION FAILED ===')
        console.error('Status:', response.status)
        console.error('Status text:', response.statusText)
        console.error('Response body:', responseText)
        
        let errorData: any = {}
        try {
          errorData = JSON.parse(responseText)
          console.error('Parsed error data:', errorData)
        } catch (e) {
          console.error('Could not parse error response as JSON:', e)
          errorData = { detail: responseText || 'Unknown error' }
        }
        
        throw new Error(errorData.detail || responseText || `HTTP ${response.status}: ${response.statusText}`)
      }

      // Parse successful response
      let data: any
      try {
        data = JSON.parse(responseText)
        console.log('=== AUTHENTICATION SUCCESS ===')
        console.log('Parsed response data:', data)
      } catch (e) {
        console.error('Failed to parse success response as JSON:', e)
        throw new Error('Invalid JSON response from server')
      }
      
      // Decode the base64 context locally to get lead info
      console.log('=== DECODING CONTEXT FOR UI ===')
      try {
        let contextStr = context
        const padding = 4 - (contextStr.length % 4)
        if (padding !== 4) {
          contextStr += '='.repeat(padding)
          console.log(`Added ${padding} padding characters for UI decoding`)
        }
        
        const decodedContext = atob(contextStr)
        const contextData = JSON.parse(decodedContext)
        console.log('Context decoded successfully for UI')
        console.log('Full context data:', contextData)
        
        const person = contextData.person
        console.log('Person data:', person)

        const leadInfo = {
          id: person.id,
          firstName: person.firstName,
          lastName: person.lastName,
          email: person.emails?.[0]?.value,
          phone: person.phones?.[0]?.value,
          stage: person.stage?.name || 'Unknown'
        }
        
        console.log('Extracted lead info:', leadInfo)

        setAuthState({
          isLoading: false,
          isAuthenticated: true,
          token: data.token,
          leadInfo
        })

        // Add welcome message
        const welcomeMessage = `Hi! I'm your FUB Follow-up Assistant. I can help you craft personalized follow-up messages for ${person.firstName} ${person.lastName}. What would you like help with?`
        console.log('Setting welcome message:', welcomeMessage)
        
        setMessages([{
          role: 'assistant',
          content: welcomeMessage
        }])
        
        console.log('=== AUTHENTICATION FLOW COMPLETE ===')

      } catch (contextError) {
        console.error('Failed to decode context for UI:', contextError)
        throw new Error('Failed to process context data')
      }

    } catch (error) {
      console.error('=== AUTHENTICATION ERROR ===')
      console.error('Error type:', typeof error)
      console.error('Error instance:', error instanceof Error ? error.constructor.name : 'Unknown')
      console.error('Error message:', error instanceof Error ? error.message : 'Unknown error')
      console.error('Full error object:', error)
      
      if (error instanceof TypeError && error.message?.includes('fetch')) {
        console.error('This looks like a network/CORS error')
        console.error('Possible causes:')
        console.error('1. Backend is down')
        console.error('2. CORS configuration issue')
        console.error('3. Network connectivity problem')
        console.error('4. Blocked by browser/firewall')
      }
      
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

    console.log('=== SENDING CHAT MESSAGE ===')
    console.log('Message:', userMessage)
    console.log('Lead context:', authState.leadInfo)
    console.log('Token (first 20 chars):', authState.token?.substring(0, 20))

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

      console.log('Chat response status:', response.status)

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const data = await response.json()
      console.log('Chat response data:', data)
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
    } catch (error) {
      console.error('Chat message error:', error)
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
          <p className="text-xs text-gray-400 mt-2">Check browser console for detailed logs</p>
        </div>
      </div>
    )
  }

  if (!authState.isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-red-50 to-white">
        <div className="text-center max-w-md mx-auto p-4">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-gray-700 mb-2">Authentication Error</h2>
          <p className="text-sm text-gray-500 mb-4">{authState.error}</p>
          <p className="text-xs text-gray-400">Check browser console for detailed logs</p>
          <div className="mt-4 text-xs text-left bg-gray-100 p-2 rounded">
            <strong>Debug Info:</strong><br/>
            URL: {window.location.href}<br/>
            Time: {new Date().toISOString()}
          </div>
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