import React from 'react';
import { Prediction } from '../../types';
import { ConfidenceBar } from './ConfidenceBar';
import { PatternBadge } from './PatternBadge';
import { useClub } from '../../hooks/useClub';

interface PredictionCardProps {
  prediction: Prediction;
}

export const PredictionCard: React.FC<PredictionCardProps> = ({ prediction }) => {
  const { clubColors } = useClub();
  
  const upsetPercentage = (prediction.final_upset_prob * 100).toFixed(1);

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-700 shadow-xl relative overflow-hidden">
      {/* Background Accent */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 blur-3xl rounded-full pointer-events-none"></div>

      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-xl font-bold text-white mb-1">
            {prediction.home_team} <span className="text-slate-500 text-sm font-normal">vs</span> {prediction.away_team}
          </h3>
          <div className="flex items-center gap-2 text-xs text-slate-400">
             <span>Prediction Confidence:</span>
             <span className={`px-2 py-0.5 rounded uppercase font-bold text-[10px] 
               ${prediction.confidence_level === 'high' ? 'bg-emerald-500/20 text-emerald-400' : 
                 prediction.confidence_level === 'medium' ? 'bg-amber-500/20 text-amber-400' : 'bg-red-500/20 text-red-400'}`}>
               {prediction.confidence_level}
             </span>
          </div>
        </div>
        
        <div className="text-right">
           <div className="text-sm text-slate-400">Favorite</div>
           <div className="font-bold text-emerald-400">{prediction.favorite}</div>
        </div>
      </div>

      {/* Power Ratings */}
      <div className="grid grid-cols-2 gap-8 mb-6">
        <ConfidenceBar label={`${prediction.favorite} Strength`} value={prediction.side_a_score} color="bg-emerald-500" />
        <ConfidenceBar label={`${prediction.underdog} Threat`} value={prediction.side_b_score} color="bg-amber-500" reverse />
      </div>

      {/* Insight Box */}
      <div className="bg-slate-800/50 rounded-lg p-4 mb-6 border border-slate-700/50">
        <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
          <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Third Knowledge Insight
        </h4>
        <p className="text-sm text-slate-300 leading-relaxed italic">
          "{prediction.key_insight}"
        </p>
      </div>

      {/* Patterns & Upset Prob */}
      <div className="flex flex-col md:flex-row justify-between items-end gap-4 border-t border-slate-700/50 pt-4">
        <div className="flex flex-wrap gap-2">
          {prediction.patterns_triggered.map((p, idx) => (
            <PatternBadge key={idx} name={p.name} />
          ))}
        </div>
        
        <div className="text-right">
          <div className="text-xs text-slate-500 mb-1">Upset Probability</div>
          <div className="text-2xl font-mono font-bold text-slate-200">
            {upsetPercentage}%
          </div>
        </div>
      </div>
    </div>
  );
};