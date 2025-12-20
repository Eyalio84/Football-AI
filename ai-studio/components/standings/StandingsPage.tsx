import React, { useEffect, useState } from 'react';
import { StandingsTable } from './StandingsTable';
import { api } from '../../services/api';
import { Standing } from '../../types';

export const StandingsPage: React.FC = () => {
  const [standings, setStandings] = useState<Standing[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStandings = async () => {
      try {
        const res = await api.getStandings();
        if (res.success && res.data) {
          setStandings(res.data);
        }
      } catch (error) {
        console.error("Failed to load table", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchStandings();
  }, []);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Premier League Table</h2>
        <span className="text-xs text-slate-500 bg-slate-900 px-3 py-1 rounded-full border border-slate-800">
          Season 2024/25
        </span>
      </div>

      <div className="glass-panel rounded-xl overflow-hidden shadow-lg">
        <StandingsTable standings={standings} />
      </div>

      <div className="flex gap-4 text-xs text-slate-400 px-2">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-blue-500 rounded-sm"></div> Champions League
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-orange-500 rounded-sm"></div> Europa League
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-red-600 rounded-sm"></div> Relegation
        </div>
      </div>
    </div>
  );
};