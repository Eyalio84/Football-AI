import React from 'react';

interface PatternBadgeProps {
  name: string;
}

export const PatternBadge: React.FC<PatternBadgeProps> = ({ name }) => {
  const formatName = (str: string) => str.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  
  return (
    <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
      <svg className="w-3 h-3 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
      {formatName(name)}
    </span>
  );
};