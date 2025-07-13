import { useEffect, useRef, useState } from 'react'
import { useAuth, useChat, useCreateNote, useFubContext } from '@fub-assistant/shared'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { PersonInfo } from './PersonInfo'

export function ChatInterface() {
  const { account, logout } = useAuth()
  const { context } = useFubContext()
  const { messages, isLoading: chatLoading, error, sendMessage, clearMessages } = useChat()
  const { createNote, isLoading: noteLoading } = useCreateNote()
  const [selectedPersonId, setSelectedPersonId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Set person ID from context if available
  useEffect(() => {
    if (context?.person?.id && !selectedPersonId) {
      setSelectedPersonId(context.person.id)
    }
  }, [context?.person?.id, selectedPersonId])

  const handleSendMessage = async (message: string) => {
    if (!selectedPersonId) {
      alert('Please select a person to chat about')
      return
    }

    await sendMessage(message, selectedPersonId)
  }

  const handleCreateNote = async (content: string) => {
    if (!selectedPersonId) return

    try {
      await createNote(content, selectedPersonId)
      // Show success message
      alert('Note created successfully!')
    } catch (error) {
      alert('Failed to create note. Please try again.')
    }
  }

  const handleNewChat = () => {
    clearMessages()
    setSelectedPersonId(context?.person?.id || null)
  }

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-gray-800">Follow-up Assistant</h1>
            <p className="text-xs text-gray-500">
              {account?.subscription_status === 'trialing' ? 'Trial' : 'Pro'}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleNewChat}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md"
            title="New Chat"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </button>
          <button
            onClick={logout}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md"
            title="Logout"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>

      {/* Person Info */}
      {selectedPersonId && context?.person && (
        <PersonInfo 
          person={context.person}
          onCreateNote={handleCreateNote}
          isCreatingNote={noteLoading}
        />
      )}

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-700 mb-2">Start a conversation</h3>
            <p className="text-sm text-gray-500 max-w-xs mx-auto">
              Ask me anything about {context?.person?.name || 'your lead'} and I'll provide personalized follow-up suggestions.
            </p>
          </div>
        ) : (
          <>
            {messages.map((message: any) => (
              <ChatMessage
                key={message.id}
                message={message}
                onCreateNote={handleCreateNote}
                isCreatingNote={noteLoading}
              />
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg p-3 max-w-xs">
                  <div className="flex items-center space-x-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-xs text-gray-500">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input */}
      <ChatInput 
        onSendMessage={handleSendMessage}
        disabled={chatLoading || !selectedPersonId}
        placeholder={
          !selectedPersonId 
            ? "Select a person to start chatting..."
            : `Ask about ${context?.person?.name || 'this lead'}...`
        }
      />
    </div>
  )
} 