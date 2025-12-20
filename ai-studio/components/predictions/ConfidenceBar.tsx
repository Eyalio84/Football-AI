import React from 'react';

interface ConfidenceBarProps {
  label: string;
  value: number; // 0-100
  color?: string;
  reverse?: boolean;
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({ label, value, color = 'bg-emerald-500', reverse = false }) => {
  return (
    <div className="w-full">
      <div className="flex justify-between mb-1">
        <span className={`text-xs font-medium text-slate-300 ${reverse ? 'order-last' : ''}`}>{label}</span>
        <span className="text-xs font-bold text-slate-100">{value}%</span>
      </div>
      <div className={`w-full bg-slate-700 rounded-full h-2.5 flex ${reverse ? 'justify-end' : 'justify-start'}`}>
        <div 
          className={`h-2.5 rounded-full ${color}`} 
          style={{ width: `${value}%` }}
        ></div>
      </div>
    </div>
  );
};