import React, { useState, useEffect, useRef } from 'react';
import { useClub } from '../../hooks/useClub';
import { api } from '../../services/api';
import { Club } from '../../types';

export const ClubSelector: React.FC = () => {
  const { currentClubId, setClubId, clubColors } = useClub();
  const [clubs, setClubs] = useState<Club[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchClubs = async () => {
      const res = await api.getClubs();
      if (res.success && res.data) {
        setClubs(res.data);
      }
    };
    fetchClubs();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedClub = clubs.find(c => c.id === currentClubId) || { name: 'Select Club' };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 rounded-full border border-slate-700 hover:border-slate-600 transition-colors text-sm"
      >
        <div 
          className="w-2 h-2 rounded-full animate-pulse"
          style={{ backgroundColor: clubColors.primary }}
        />
        <span className="font-medium text-slate-200 truncate max-w-[100px] sm:max-w-none">
          {selectedClub.name}
        </span>
        <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-slate-800 border border-slate-700 rounded-xl shadow-xl overflow-hidden z-50 max-h-96 overflow-y-auto scrollbar-hide">
          <div className="px-4 py-2 bg-slate-900/50 border-b border-slate-700 text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Select Persona
          </div>
          {clubs.map((club) => (
            <button
              key={club.id}
              onClick={() => {
                setClubId(club.id);
                setIsOpen(false);
              }}
              className={`w-full text-left px-4 py-3 text-sm flex items-center gap-3 hover:bg-slate-700/50 transition-colors ${
                currentClubId === club.id ? 'bg-slate-700/30 text-white' : 'text-slate-300'
              }`}
            >
              {currentClubId === club.id && (
                <div 
                  className="w-1.5 h-1.5 rounded-full"
                  style={{ backgroundColor: clubColors.primary }}
                />
              )}
              {club.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};