import { ClubColors } from '../types';

export const CLUB_COLORS: Record<string, ClubColors> = {
  arsenal: { primary: '#EF0107', secondary: '#063672' },
  chelsea: { primary: '#034694', secondary: '#DBA111' },
  liverpool: { primary: '#C8102E', secondary: '#00B2A9' },
  manchester_united: { primary: '#DA291C', secondary: '#FBE122' },
  manchester_city: { primary: '#6CABDD', secondary: '#1C2C5B' },
  tottenham: { primary: '#132257', secondary: '#FFFFFF' },
  newcastle: { primary: '#241F20', secondary: '#FFFFFF' },
  west_ham: { primary: '#7A263A', secondary: '#1BB1E7' },
  everton: { primary: '#003399', secondary: '#FFFFFF' },
  brighton: { primary: '#0057B8', secondary: '#FFCD00' },
  aston_villa: { primary: '#95BFE5', secondary: '#670E36' },
  wolves: { primary: '#FDB913', secondary: '#231F20' },
  crystal_palace: { primary: '#1B458F', secondary: '#C4122E' },
  fulham: { primary: '#000000', secondary: '#CC0000' },
  nottingham_forest: { primary: '#DD0000', secondary: '#FFFFFF' },
  brentford: { primary: '#E30613', secondary: '#FBB800' },
  bournemouth: { primary: '#DA291C', secondary: '#000000' },
  leicester: { primary: '#003090', secondary: '#FDBE11' },
  ipswich: { primary: '#3A64A3', secondary: '#FFFFFF' },
  southampton: { primary: '#D71920', secondary: '#130C0E' },
  analyst: { primary: '#10b981', secondary: '#0f172a' }
};

export const DEFAULT_CLUB = 'arsenal';