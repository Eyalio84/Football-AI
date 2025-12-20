import React from 'react';
import { useChat } from '../../hooks/useChat';
import { ChatHistory } from './ChatHistory';
import { ChatInput } from './ChatInput';

export const ChatPage: React.FC = () => {
  const { messages, sendMessage, isLoading } = useChat();

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] md:h-[calc(100vh-180px)] glass-panel rounded-2xl overflow-hidden shadow-2xl">
      <div className="bg-slate-900/50 p-3 border-b border-slate-700/50 flex justify-center md:hidden">
        <span className="text-xs font-medium text-slate-400">Supported by your club persona</span>
      </div>
      <ChatHistory messages={messages} isLoading={isLoading} />
      <ChatInput onSend={sendMessage} isLoading={isLoading} />
    </div>
  );
};