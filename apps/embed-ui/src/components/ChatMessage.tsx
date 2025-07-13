
import type { ChatMessage as ChatMessageType } from '@fub-assistant/shared'

interface ChatMessageProps {
  message: ChatMessageType
  onCreateNote: (content: string) => Promise<void>
  isCreatingNote: boolean
}

export function ChatMessage({ message, onCreateNote, isCreatingNote }: ChatMessageProps) {
  const isUser = message.role === 'user'

  const handleCreateNote = () => {
    if (message.role === 'assistant') {
      onCreateNote(message.content)
    }
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            isUser ? 'bg-blue-500' : 'bg-gray-100'
          }`}>
            {isUser ? (
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            ) : (
              <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            )}
          </div>
        </div>

        {/* Message Content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <div className={`rounded-lg px-4 py-2 ${
            isUser 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-800'
          }`}>
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          </div>
          
          {/* Timestamp and Actions */}
          <div className="flex items-center space-x-2 mt-1">
            <span className="text-xs text-gray-400">
              {new Date(message.timestamp).toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </span>
            
            {/* Create Note Button for AI responses */}
            {!isUser && (
              <button
                onClick={handleCreateNote}
                disabled={isCreatingNote}
                className="text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
                title="Create note in Follow Up Boss"
              >
                {isCreatingNote ? (
                  <>
                    <div className="w-3 h-3 border border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                    <span>Creating...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    <span>Create Note</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
} 