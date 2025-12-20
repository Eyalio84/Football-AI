import React, { useEffect, useState } from 'react';
import { PredictionCard } from './PredictionCard';
import { api } from '../../services/api';
import { Prediction, Game } from '../../types';

export const PredictionsPage: React.FC = () => {
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [fixtures, setFixtures] = useState<Game[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // For this demo, we'll fetch one main prediction and list fixtures to "click"
  useEffect(() => {
    const init = async () => {
      setIsLoading(true);
      try {
        const fixRes = await api.getFixturesUpcoming();
        if (fixRes.success && fixRes.data && fixRes.data.length > 0) {
          setFixtures(fixRes.data);
          // Auto-load prediction for first game
          const firstGame = fixRes.data[0];
          const predRes = await api.getPrediction(firstGame.home_team_name, firstGame.away_team_name);
          if (predRes.success) setPrediction(predRes.data);
        }
      } finally {
        setIsLoading(false);
      }
    };
    init();
  }, []);

  const handlePredictClick = async (home: string, away: string) => {
    setPrediction(null); // Clear current
    setIsLoading(true);
    try {
      const res = await api.getPrediction(home, away);
      if (res.success) setPrediction(res.data);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Match Intelligence</h2>
        <p className="text-slate-400">Using 6 interaction patterns to predict outcomes with 62.9% accuracy.</p>
      </div>

      {isLoading && !prediction ? (
        <div className="h-64 glass-panel rounded-2xl animate-pulse"></div>
      ) : prediction ? (
        <PredictionCard prediction={prediction} />
      ) : (
        <div className="text-center p-12 glass-panel rounded-2xl text-slate-500">
          Select a fixture to analyze.
        </div>
      )}

      <div className="mt-8">
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Select Fixture to Analyze</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {fixtures.map((game) => (
            <button 
              key={game.id}
              onClick={() => handlePredictClick(game.home_team_name, game.away_team_name)}
              className="bg-slate-800 hover:bg-slate-700 p-4 rounded-xl border border-slate-700 transition-all flex justify-between items-center group"
            >
              <div className="flex flex-col items-start">
                <span className="font-bold text-slate-200 group-hover:text-emerald-400 transition-colors">
                  {game.home_team_name} vs {game.away_team_name}
                </span>
                <span className="text-xs text-slate-500">{game.venue}</span>
              </div>
              <svg className="w-5 h-5 text-slate-500 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};