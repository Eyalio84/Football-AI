import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ClubColors } from '../types';
import { CLUB_COLORS, DEFAULT_CLUB } from '../constants/clubs';
import { MOCK_CLUBS } from '../constants/mock-data';

interface ClubContextType {
  currentClubId: string;
  setClubId: (id: string) => void;
  clubColors: ClubColors;
  clubName: string;
}

const ClubContext = createContext<ClubContextType | undefined>(undefined);

export const ClubProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Try to load from local storage
  const [currentClubId, setCurrentClubId] = useState<string>(() => {
    return localStorage.getItem('soccer_ai_club') || DEFAULT_CLUB;
  });

  const [clubColors, setClubColors] = useState<ClubColors>(CLUB_COLORS[DEFAULT_CLUB]);
  const [clubName, setClubName] = useState<string>('Arsenal');

  useEffect(() => {
    // Update local storage
    localStorage.setItem('soccer_ai_club', currentClubId);
    
    // Update colors
    const colors = CLUB_COLORS[currentClubId] || CLUB_COLORS.analyst;
    setClubColors(colors);
    
    // Update name
    const club = MOCK_CLUBS.find(c => c.id === currentClubId);
    setClubName(club ? club.name : 'Neutral Analyst');
    
  }, [currentClubId]);

  const setClubId = (id: string) => {
    setCurrentClubId(id);
  };

  return React.createElement(
    ClubContext.Provider,
    { value: { currentClubId, setClubId, clubColors, clubName } },
    children
  );
};

export const useClub = () => {
  const context = useContext(ClubContext);
  if (context === undefined) {
    throw new Error('useClub must be used within a ClubProvider');
  }
  return context;
};