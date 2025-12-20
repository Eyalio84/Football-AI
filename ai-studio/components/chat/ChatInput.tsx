import React, { useState, KeyboardEvent } from 'react';
import { useClub } from '../../hooks/useClub';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend, isLoading }) => {
  const [input, setInput] = useState('');
  const { clubColors } = useClub();

  const handleSend = () => {
    if (input.trim() && !isLoading) {
      onSend(input);
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-4 bg-slate-900/80 backdrop-blur border-t border-slate-800 sticky bottom-0">
      <div className="max-w-4xl mx-auto relative flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about the match, rivals, or tactics..."
          disabled={isLoading}
          className="w-full bg-slate-800 text-slate-100 placeholder-slate-500 border border-slate-700 rounded-full px-5 py-3 pr-12 focus:outline-none focus:ring-2 focus:border-transparent transition-all shadow-sm"
          style={{ '--tw-ring-color': clubColors.primary } as React.CSSProperties}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          className="absolute right-2 p-2 rounded-full text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:brightness-110 shadow-md"
          style={{ backgroundColor: clubColors.primary }}
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
    </div>
  );
};