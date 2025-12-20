import React from 'react';
import { Game } from '../../types';
import { LiveIndicator } from './LiveIndicator';
import { useClub } from '../../hooks/useClub';

interface FixtureCardProps {
  game: Game;
}

export const FixtureCard: React.FC<FixtureCardProps> = ({ game }) => {
  const { currentClubId, clubColors } = useClub();
  
  // Highlight if it involves my club
  const isMyClubMatch = [game.home_team_id, game.away_team_id].some(id => {
    // Basic mock check, normally compare IDs carefully
    return false; // Assuming mock IDs match logic handled elsewhere or complex
  }) || game.home_team_name.toLowerCase().includes(currentClubId.replace('_',' ')) 
     || game.away_team_name.toLowerCase().includes(currentClubId.replace('_',' '));

  return (
    <div 
      className={`glass-panel p-4 rounded-xl border transition-all duration-300 hover:shadow-lg
        ${isMyClubMatch ? 'ring-1 ring-offset-1 ring-offset-slate-950' : 'border-slate-700/50'}`}
      style={isMyClubMatch ? { '--tw-ring-color': clubColors.primary } as React.CSSProperties : {}}
    >
      <div className="flex justify-between items-center mb-4">
        <div className="text-xs text-slate-400 font-medium uppercase tracking-wide">
          {game.competition}
        </div>
        {game.status === 'live' ? (
          <LiveIndicator />
        ) : (
          <div className="text-xs text-slate-500">
            {game.status === 'finished' ? 'FT' : game.time}
          </div>
        )}
      </div>

      <div className="flex justify-between items-center gap-4">
        {/* Home Team */}
        <div className="flex-1 flex flex-col items-center gap-2">
          <div className="w-12 h-12 rounded-full bg-slate-700/50 flex items-center justify-center text-slate-300 font-bold border border-slate-600">
            {game.home_team_short?.[0] || 'H'}
          </div>
          <span className="text-sm font-semibold text-center text-white leading-tight">{game.home_team_name}</span>
        </div>

        {/* Score / VS */}
        <div className="flex flex-col items-center min-w-[60px]">
          {game.status !== 'scheduled' ? (
            <div className="text-2xl font-bold text-white tracking-widest bg-slate-900/50 px-3 py-1 rounded-lg border border-slate-700">
              {game.home_score} - {game.away_score}
            </div>
          ) : (
            <div className="text-slate-500 font-bold text-xl">VS</div>
          )}
        </div>

        {/* Away Team */}
        <div className="flex-1 flex flex-col items-center gap-2">
          <div className="w-12 h-12 rounded-full bg-slate-700/50 flex items-center justify-center text-slate-300 font-bold border border-slate-600">
            {game.away_team_short?.[0] || 'A'}
          </div>
          <span className="text-sm font-semibold text-center text-white leading-tight">{game.away_team_name}</span>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-700/50 text-center">
        <p className="text-xs text-slate-500 truncate">
          {game.venue}
        </p>
      </div>
    </div>
  );
};