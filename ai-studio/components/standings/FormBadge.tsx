import React from 'react';

interface FormBadgeProps {
  result: string; // 'W', 'D', 'L'
}

export const FormBadge: React.FC<FormBadgeProps> = ({ result }) => {
  let bgColor = 'bg-slate-700';
  let textColor = 'text-slate-300';

  switch (result.toUpperCase()) {
    case 'W':
      bgColor = 'bg-emerald-500/20 border-emerald-500/30';
      textColor = 'text-emerald-400';
      break;
    case 'D':
      bgColor = 'bg-amber-500/20 border-amber-500/30';
      textColor = 'text-amber-400';
      break;
    case 'L':
      bgColor = 'bg-red-500/20 border-red-500/30';
      textColor = 'text-red-400';
      break;
  }

  return (
    <span className={`inline-flex items-center justify-center w-6 h-6 rounded text-xs font-bold border ${bgColor} ${textColor} mx-0.5`}>
      {result}
    </span>
  );
};