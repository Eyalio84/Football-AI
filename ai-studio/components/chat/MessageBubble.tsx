import React from 'react';
import { ChatMessage } from '../../types';
import { useClub } from '../../hooks/useClub';

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const { clubColors, clubName } = useClub();
  const isUser = message.role === 'user';

  return (
    <div className={`flex w-full mb-6 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[85%] md:max-w-[70%] ${isUser ? 'flex-row-reverse' : 'flex-row'} gap-3`}>
        {/* Avatar */}
        <div 
          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shadow-md
            ${isUser ? 'bg-slate-700 text-slate-300' : 'text-white'}`}
          style={!isUser ? { backgroundColor: clubColors.primary } : {}}
        >
          {isUser ? 'YOU' : 'AI'}
        </div>

        {/* Content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium text-slate-400">
              {isUser ? 'You' : `${clubName} Fan`}
            </span>
            {!isUser && message.confidence && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-800 text-emerald-400 border border-emerald-900/30">
                {(message.confidence * 100).toFixed(0)}% Conf
              </span>
            )}
          </div>
          
          <div 
            className={`px-4 py-3 rounded-2xl shadow-sm text-sm md:text-base leading-relaxed whitespace-pre-wrap
              ${isUser 
                ? 'bg-slate-800 text-slate-100 rounded-tr-sm border border-slate-700' 
                : 'bg-gradient-to-br from-slate-800 to-slate-900/80 backdrop-blur-sm text-slate-100 rounded-tl-sm border border-slate-700/50'
              }`}
            style={!isUser ? { borderLeft: `3px solid ${clubColors.primary}` } : {}}
          >
            {message.content}
          </div>
          
          <span className="text-[10px] text-slate-600 mt-1 px-1">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
    </div>
  );
};