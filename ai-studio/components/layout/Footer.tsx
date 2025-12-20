import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 border-t border-slate-800 py-6 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="mb-4 md:mb-0">
            <span className="text-slate-400 text-sm font-medium">Soccer-AI</span>
            <span className="text-slate-600 text-sm mx-2">|</span>
            <span className="text-slate-500 text-xs">The emotionally intelligent companion</span>
          </div>
          <div className="text-slate-600 text-xs">
            Data provided by Premier League API (Mock)
          </div>
        </div>
      </div>
    </footer>
  );
};