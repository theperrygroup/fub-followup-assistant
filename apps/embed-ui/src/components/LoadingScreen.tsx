

export function LoadingScreen() {
  return (
    <div className="flex items-center justify-center h-full bg-gradient-to-br from-blue-50 to-white">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <h2 className="text-lg font-semibold text-gray-700 mb-2">FUB Follow-up Assistant</h2>
        <p className="text-sm text-gray-500 loading-dots">Loading</p>
      </div>
    </div>
  )
} 