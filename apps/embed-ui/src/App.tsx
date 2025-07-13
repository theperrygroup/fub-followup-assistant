import { useState } from 'react'

function App() {
  const [message] = useState('Connecting to FUB Follow-up Assistant...')

  return (
    <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-50 to-white">
      <div className="text-center max-w-md p-8">
        <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-800 mb-2">
          FUB Follow-up Assistant
        </h1>
        <p className="text-gray-600 mb-4">
          AI-powered follow-up assistance for your leads
        </p>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-sm text-gray-500">{message}</p>
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-400">
            API Endpoint: https://fub-followup-assistant-production.up.railway.app
          </p>
          <p className="text-xs text-green-600 mt-1">
            ✅ Embed UI is running successfully
          </p>
        </div>
      </div>
    </div>
  )
}

export default App 