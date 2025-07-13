import { useState, useRef, useEffect } from 'react'

interface ChatInputProps {
  onSendMessage: (message: string) => Promise<void>
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({ onSendMessage, disabled = false, placeholder = "Ask a question..." }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const [isSending, setIsSending] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`
    }
  }, [message])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const trimmedMessage = message.trim()
    if (!trimmedMessage || isSending || disabled) return

    setIsSending(true)
    setMessage('')

    try {
      await onSendMessage(trimmedMessage)
    } catch (error) {
      console.error('Failed to send message:', error)
      // Restore message if sending failed
      setMessage(trimmedMessage)
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  const isSubmitDisabled = disabled || isSending || !message.trim()

  return (
    <div className="border-t bg-white p-4">
      <form onSubmit={handleSubmit} className="flex items-end space-x-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled || isSending}
            className="w-full resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500 max-h-[120px]"
            rows={1}
          />
          {message.length > 200 && (
            <div className="absolute bottom-1 right-1 text-xs text-gray-400">
              {message.length}/400
            </div>
          )}
        </div>
        
        <button
          type="submit"
          disabled={isSubmitDisabled}
          className="flex-shrink-0 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="Send message"
        >
          {isSending ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          )}
        </button>
      </form>
      
      <p className="text-xs text-gray-400 mt-2">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  )
} 