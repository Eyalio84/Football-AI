import { useState, useEffect } from 'react'
import { ChatContainer } from '@/components/Chat/ChatContainer'
import { ClubSelection } from '@/components/Chat/ClubSelection'
import { useChat } from '@/hooks/useChat'
import { useClubTheme } from '@/config/ClubThemeProvider'

export function Chat() {
  const [selectedClub, setSelectedClub] = useState<string | null>(null)
  const { setClubId } = useClubTheme()
  const {
    messages,
    conversationId,
    isLoading,
    sendMessage,
    clearChat,
    streamingEnabled,
    toggleStreaming,
  } = useChat(selectedClub || undefined)

  // Sync club selection with global theme
  useEffect(() => {
    setClubId(selectedClub)
  }, [selectedClub, setClubId])

  const handleClubSelect = (clubId: string) => {
    setSelectedClub(clubId)
  }

  const handleChangeClub = () => {
    setSelectedClub(null)
    clearChat()
  }

  // Show club selection first
  if (!selectedClub) {
    return <ClubSelection onSelectClub={handleClubSelect} />
  }

  // Show chat interface after club selected
  return (
    <div className="h-[calc(100vh-8rem)]">
      <ChatContainer
        messages={messages}
        onSendMessage={sendMessage}
        isLoading={isLoading}
        conversationId={conversationId}
        onClearChat={handleChangeClub}
        clubId={selectedClub}
        streamingEnabled={streamingEnabled}
        onToggleStreaming={toggleStreaming}
      />
    </div>
  )
}
