import { useEffect, useState } from 'react'
import { useAuth, useFubContext } from '@fub-assistant/shared'
import { AuthScreen } from './components/AuthScreen'
import { ChatInterface } from './components/ChatInterface'
import { LoadingScreen } from './components/LoadingScreen'
import { SubscriptionRequiredScreen } from './components/SubscriptionRequiredScreen'

function App() {
  const { isAuthenticated, isLoading, account, login } = useAuth()
  const { context } = useFubContext()
  const [isInitializing, setIsInitializing] = useState(true)

  useEffect(() => {
    // Mark as initialized after a short delay to allow hooks to settle
    const timer = setTimeout(() => {
      setIsInitializing(false)
    }, 100)
    
    return () => clearTimeout(timer)
  }, [])

  const handleLogin = async (contextData: string, signature: string) => {
    try {
      await login(contextData, signature)
    } catch (error) {
      console.error('Login failed:', error)
    }
  }

  // Show loading while initializing
  if (isInitializing || isLoading) {
    return <LoadingScreen />
  }

  // Show auth screen if not authenticated
  if (!isAuthenticated) {
    return (
      <AuthScreen 
        onLogin={handleLogin}
        context={context}
      />
    )
  }

  // Check subscription status
  if (account?.subscription_status !== 'active' && 
      account?.subscription_status !== 'trialing') {
    return <SubscriptionRequiredScreen />
  }

  // Show main chat interface
  return <ChatInterface />
}

export default App 