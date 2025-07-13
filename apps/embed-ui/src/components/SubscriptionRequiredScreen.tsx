

export function SubscriptionRequiredScreen() {
  const handleUpgrade = () => {
    // Open parent window to billing portal
    const message = {
      type: 'fub_open_billing',
      timestamp: Date.now()
    }
    window.parent.postMessage(message, '*')
  }

  return (
    <div className="flex items-center justify-center h-full bg-gradient-to-br from-orange-50 to-white p-6">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
        <div className="mb-6">
          <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">
            Subscription Required
          </h1>
          <p className="text-gray-600 mb-4">
            To use the FUB Follow-up Assistant, you need an active subscription.
          </p>
        </div>

        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h3 className="font-semibold text-blue-800 mb-2">Features Include:</h3>
            <ul className="text-sm text-blue-700 space-y-1 text-left">
              <li>• AI-powered follow-up suggestions</li>
              <li>• Automatic note creation</li>
              <li>• Lead context analysis</li>
              <li>• Real estate expertise</li>
            </ul>
          </div>

          <button
            onClick={handleUpgrade}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium transition-colors"
          >
            Upgrade Subscription
          </button>

          <p className="text-xs text-gray-500">
            You'll be redirected to manage your subscription
          </p>
        </div>
      </div>
    </div>
  )
} 