import React, { useEffect, useRef } from 'react';
import { ChatMessage } from '../../types';
import { MessageBubble } from './MessageBubble';

interface ChatHistoryProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({ messages, isLoading }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-grow overflow-y-auto px-4 py-6 scrollbar-hide">
      {messages.length === 0 ? (
        <div className="h-full flex flex-col items-center justify-center text-slate-500 opacity-60">
          <svg className="w-16 h-16 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <p>Start the banter.</p>
        </div>
      ) : (
        messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))
      )}
      
      {isLoading && (
        <div className="flex w-full mb-6 justify-start animate-pulse">
           <div className="flex max-w-[85%] flex-row gap-3">
             <div className="w-8 h-8 rounded-full bg-slate-800" />
             <div className="flex flex-col items-start">
               <div className="h-10 w-32 bg-slate-800 rounded-2xl rounded-tl-sm" />
             </div>
           </div>
        </div>
      )}
      
      <div ref={bottomRef} />
    </div>
  );
};