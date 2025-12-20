import React from 'react';
import { Standing } from '../../types';
import { FormBadge } from './FormBadge';
import { ZoneIndicator } from './ZoneIndicator';
import { useClub } from '../../hooks/useClub';

interface StandingsTableProps {
  standings: Standing[];
}

export const StandingsTable: React.FC<StandingsTableProps> = ({ standings }) => {
  const { currentClubId, clubColors } = useClub();

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="text-xs font-semibold text-slate-400 border-b border-slate-700 bg-slate-800/50">
            <th className="p-3 w-12 text-center">Pos</th>
            <th className="p-3">Club</th>
            <th className="p-3 text-center">MP</th>
            <th className="p-3 text-center">W</th>
            <th className="p-3 text-center">D</th>
            <th className="p-3 text-center">L</th>
            <th className="p-3 text-center">GF</th>
            <th className="p-3 text-center">GA</th>
            <th className="p-3 text-center">GD</th>
            <th className="p-3 text-center">Pts</th>
            <th className="p-3 text-center hidden md:table-cell">Form</th>
          </tr>
        </thead>
        <tbody className="text-sm">
          {standings.map((team) => {
            const isMyClub = team.team_id.toString() === currentClubId || 
                           team.team_name.toLowerCase().replace(/\s/g, '_') === currentClubId;

            return (
              <tr 
                key={team.team_id}
                className={`group border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors relative
                  ${isMyClub ? 'bg-slate-800/60' : ''}`}
              >
                <td className="p-3 text-center relative font-medium text-slate-500">
                  <ZoneIndicator position={team.position} />
                  {team.position}
                </td>
                <td className="p-3 font-semibold text-white flex items-center gap-3">
                  {/* Placeholder Logo */}
                  <div className={`w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center text-[10px] text-slate-300
                    ${isMyClub ? 'ring-2 ring-offset-2 ring-offset-slate-900' : ''}`}
                    style={isMyClub ? { '--tw-ring-color': clubColors.primary } as React.CSSProperties : {}}
                  >
                    {team.short_name?.[0]}
                  </div>
                  {team.team_name}
                </td>
                <td className="p-3 text-center text-slate-300">{team.played}</td>
                <td className="p-3 text-center text-slate-400">{team.won}</td>
                <td className="p-3 text-center text-slate-400">{team.drawn}</td>
                <td className="p-3 text-center text-slate-400">{team.lost}</td>
                <td className="p-3 text-center text-slate-400 hidden sm:table-cell">{team.goals_for}</td>
                <td className="p-3 text-center text-slate-400 hidden sm:table-cell">{team.goals_against}</td>
                <td className="p-3 text-center text-slate-300">{team.goal_difference}</td>
                <td className="p-3 text-center font-bold text-white text-base">{team.points}</td>
                <td className="p-3 text-center hidden md:flex justify-center items-center h-full">
                  <div className="flex">
                    {team.form?.split('').map((res, idx) => (
                      <FormBadge key={idx} result={res} />
                    ))}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};