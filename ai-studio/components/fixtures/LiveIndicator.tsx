import React from 'react';

export const LiveIndicator: React.FC = () => {
  return (
    <div className="flex items-center gap-1.5 px-2 py-0.5 bg-red-500/10 border border-red-500/20 rounded-full">
      <div className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
      </div>
      <span className="text-[10px] font-bold text-red-500 uppercase tracking-wide">Live</span>
    </div>
  );
};