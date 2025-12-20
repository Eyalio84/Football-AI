import { useState, useCallback, useEffect } from 'react';
import { ChatMessage } from '../types';
import { api } from '../services/api';
import { useClub } from './useClub';

export const useChat = () => {
  const { currentClubId } = useClub();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);

  // Clear chat or add greeting when club changes
  useEffect(() => {
    // Only reset if we actually change clubs to avoid wiping on refresh (though context handles that)
    // For this demo, we'll keep history but add a system-like separator or just a new greeting
    const greeting: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: `Alright? I'm ready to talk about the ${currentClubId === 'analyst' ? 'football' : 'club'}. What's on your mind?`,
      timestamp: new Date(),
      club: currentClubId
    };
    
    // Optional: Wipe history on club switch to keep persona context clean
    setMessages([greeting]);
    setConversationId(undefined); // Start new convo context
  }, [currentClubId]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    // Add user message
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const result = await api.chat(content, currentClubId, conversationId);
      
      if (result.success && result.data) {
        const aiMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: result.data.response,
          timestamp: new Date(),
          club: currentClubId,
          confidence: result.data.confidence
        };
        
        setMessages(prev => [...prev, aiMsg]);
        setConversationId(result.data.conversation_id);
      } else {
        // Handle error visually
        const errorMsg: ChatMessage = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: "Sorry mate, lost my train of thought. Try again?",
            timestamp: new Date(),
            club: currentClubId
        };
        setMessages(prev => [...prev, errorMsg]);
      }
    } catch (err) {
      console.error(err);
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: "Can't connect to the pitch right now. Check your connection.",
        timestamp: new Date(),
        club: currentClubId
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [currentClubId, conversationId]);

  return { messages, sendMessage, isLoading };
};