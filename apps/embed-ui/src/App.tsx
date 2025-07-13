import { useState } from 'react'

function App() {
  const [isLoading] = useState(true)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-50 to-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-lg font-semibold text-gray-700 mb-2">FUB Follow-up Assistant</h2>
          <p className="text-sm text-gray-500">Loading embed interface...</p>
          <p className="text-xs text-gray-400 mt-4">
            API: https://fub-followup-assistant-production.up.railway.app
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-center h-screen">
      <h1>FUB Chat Interface</h1>
    </div>
  )
}

export default App 