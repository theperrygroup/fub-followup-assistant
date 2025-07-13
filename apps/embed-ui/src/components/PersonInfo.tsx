
import type { FubContext } from '@fub-assistant/shared'

interface PersonInfoProps {
  person: NonNullable<FubContext['person']>
  onCreateNote: (content: string) => Promise<void>
  isCreatingNote: boolean
}

export function PersonInfo({ person, onCreateNote, isCreatingNote }: PersonInfoProps) {
  const handleQuickNote = (template: string) => {
    onCreateNote(template)
  }

  const quickNoteTemplates = [
    "Reached out via phone - left voicemail",
    "Sent follow-up email with property details",
    "Scheduled showing for next week",
    "Client needs more time to decide",
    "Interested in similar properties"
  ]

  return (
    <div className="border-b bg-gray-50 p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-blue-600 font-semibold text-sm">
                {person.name.split(' ').map((n: string) => n[0]).join('').toUpperCase()}
              </span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-800">{person.name}</h3>
              <div className="flex items-center space-x-3 text-xs text-gray-500">
                {person.email && (
                  <span className="flex items-center space-x-1">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                    </svg>
                    <span>{person.email}</span>
                  </span>
                )}
                {person.phone && (
                  <span className="flex items-center space-x-1">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                    <span>{person.phone}</span>
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center space-x-2">
          <div className="relative group">
            <button className="p-2 text-gray-400 hover:text-gray-600 rounded-md">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
              </svg>
            </button>
            
            {/* Quick Note Dropdown */}
            <div className="absolute right-0 top-8 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-10 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
              <div className="p-3">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Quick Notes</h4>
                <div className="space-y-1">
                  {quickNoteTemplates.map((template, index) => (
                    <button
                      key={index}
                      onClick={() => handleQuickNote(template)}
                      disabled={isCreatingNote}
                      className="w-full text-left px-2 py-1 text-xs text-gray-600 hover:bg-gray-50 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {template}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-200">
        <div className="flex items-center space-x-4 text-xs text-gray-500">
          <span className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            <span>Active Lead</span>
          </span>
          <span>ID: {person.id}</span>
        </div>
        
        {isCreatingNote && (
          <div className="flex items-center space-x-2 text-xs text-blue-600">
            <div className="w-3 h-3 border border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <span>Creating note...</span>
          </div>
        )}
      </div>
    </div>
  )
} 