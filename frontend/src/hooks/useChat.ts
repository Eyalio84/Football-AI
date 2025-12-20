/**
 * useChat Hook
 *
 * Manages chat state and handles sending/receiving messages.
 * Supports both instant and streaming response modes.
 */

import { useState, useCallback, useRef } from 'react'
import type { Message, ChatState } from '../types'
import { sendChatMessage, sendChatMessageStream } from '../services/api'

interface ExtendedChatState extends ChatState {
  streamingEnabled: boolean
}

export function useChat(clubId?: string) {
  const [state, setState] = useState<ExtendedChatState>({
    messages: [],
    conversationId: null,
    isLoading: false,
    error: null,
    streamingEnabled: true, // Default to streaming mode
  })

  // Track current streaming message ID
  const streamingMessageIdRef = useRef<string | null>(null)

  /**
   * Send a message to the AI with fan persona
   * Uses streaming or instant mode based on state
   */
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return

    // Handle /stream toggle command
    if (content.trim().toLowerCase() === '/stream') {
      setState((prev) => ({
        ...prev,
        streamingEnabled: !prev.streamingEnabled,
      }))
      // Add system message to show toggle status
      const toggleMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `🔄 Streaming mode ${state.streamingEnabled ? 'disabled' : 'enabled'}`,
        timestamp: new Date(),
      }
      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, toggleMessage],
      }))
      return
    }

    // Create user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    }

    // Create placeholder for bot response (shows "typing" indicator)
    const botMessageId = crypto.randomUUID()
    const botMessagePlaceholder: Message = {
      id: botMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    }

    // Update UI immediately with user message + loading indicator
    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, userMessage, botMessagePlaceholder],
      isLoading: true,
      error: null,
    }))

    // Use streaming or instant mode
    if (state.streamingEnabled) {
      // STREAMING MODE
      streamingMessageIdRef.current = botMessageId

      await sendChatMessageStream(
        content,
        state.conversationId || undefined,
        clubId,
        // onChunk - append text as it arrives
        (text: string) => {
          setState((prev) => ({
            ...prev,
            messages: prev.messages.map((msg) =>
              msg.id === botMessageId
                ? { ...msg, content: msg.content + text, isLoading: false }
                : msg
            ),
          }))
        },
        // onDone - finalize
        (conversationId: string) => {
          streamingMessageIdRef.current = null
          setState((prev) => ({
            ...prev,
            conversationId: conversationId || prev.conversationId,
            isLoading: false,
          }))
        },
        // onError
        (error: string) => {
          streamingMessageIdRef.current = null
          setState((prev) => ({
            ...prev,
            messages: prev.messages.map((msg) =>
              msg.id === botMessageId
                ? { ...msg, content: `❌ Error: ${error}`, isLoading: false }
                : msg
            ),
            isLoading: false,
            error,
          }))
        }
      )
    } else {
      // INSTANT MODE (original behavior)
      try {
        const response = await sendChatMessage(
          content,
          state.conversationId || undefined,
          clubId
        )

        setState((prev) => ({
          ...prev,
          messages: prev.messages.map((msg) =>
            msg.id === botMessageId
              ? {
                  ...msg,
                  content: response.response,
                  sources: response.sources,
                  isLoading: false,
                }
              : msg
          ),
          conversationId: response.conversation_id,
          isLoading: false,
        }))
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : 'Failed to send message'

        setState((prev) => ({
          ...prev,
          messages: prev.messages.map((msg) =>
            msg.id === botMessageId
              ? {
                  ...msg,
                  content: `❌ Error: ${errorMessage}`,
                  isLoading: false,
                }
              : msg
          ),
          isLoading: false,
          error: errorMessage,
        }))
      }
    }
  }, [state.conversationId, state.streamingEnabled, clubId])

  /**
   * Clear all messages and start a new conversation
   */
  const clearChat = useCallback(() => {
    setState((prev) => ({
      messages: [],
      conversationId: null,
      isLoading: false,
      error: null,
      streamingEnabled: prev.streamingEnabled, // Preserve streaming preference
    }))
  }, [])

  /**
   * Toggle streaming mode
   */
  const toggleStreaming = useCallback(() => {
    setState((prev) => ({
      ...prev,
      streamingEnabled: !prev.streamingEnabled,
    }))
  }, [])

  /**
   * Retry the last failed message
   */
  const retryLastMessage = useCallback(() => {
    const lastUserMessage = [...state.messages]
      .reverse()
      .find((msg) => msg.role === 'user')

    if (lastUserMessage) {
      // Remove failed bot response
      setState((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -1),
      }))
      // Retry
      sendMessage(lastUserMessage.content)
    }
  }, [state.messages, sendMessage])

  return {
    messages: state.messages,
    conversationId: state.conversationId,
    isLoading: state.isLoading,
    error: state.error,
    streamingEnabled: state.streamingEnabled,
    sendMessage,
    clearChat,
    toggleStreaming,
    retryLastMessage,
  }
}
