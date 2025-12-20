import React, { useEffect, useState } from 'react';
import { FixtureCard } from './FixtureCard';
import { api } from '../../services/api';
import { Game } from '../../types';

export const FixturesPage: React.FC = () => {
  const [fixtures, setFixtures] = useState<Game[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<'today' | 'upcoming'>('today');

  useEffect(() => {
    const loadFixtures = async () => {
      setIsLoading(true);
      try {
        const res = filter === 'today' ? await api.getFixturesToday() : await api.getFixturesUpcoming();
        if (res.success && res.data) {
          setFixtures(res.data);
        }
      } finally {
        setIsLoading(false);
      }
    };
    loadFixtures();
  }, [filter]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-2xl font-bold text-white">Match Center</h2>
        
        <div className="flex bg-slate-800 p-1 rounded-lg border border-slate-700">
          <button
            onClick={() => setFilter('today')}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
              filter === 'today' ? 'bg-slate-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Today
          </button>
          <button
            onClick={() => setFilter('upcoming')}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
              filter === 'upcoming' ? 'bg-slate-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Upcoming
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1,2,3].map(i => (
             <div key={i} className="h-48 bg-slate-800/50 rounded-xl animate-pulse border border-slate-700/50"></div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {fixtures.map(game => (
            <FixtureCard key={game.id} game={game} />
          ))}
          {fixtures.length === 0 && (
            <div className="col-span-full text-center py-12 text-slate-500">
              No fixtures scheduled for {filter === 'today' ? 'today' : 'the upcoming period'}.
            </div>
          )}
        </div>
      )}
    </div>
  );
};