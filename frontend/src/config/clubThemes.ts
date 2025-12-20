/**
 * Club Theme Palettes
 *
 * All 20 Premier League clubs + neutral analyst mode.
 * These drive CSS custom properties that shift the entire UI
 * to match the selected club's identity.
 */

export interface ClubPalette {
  primary: string
  secondary: string
  accent: string
  gradient: string
  glowColor: string   // For stadium floodlight effect
  textOnPrimary: string
}

export const CLUB_PALETTES: Record<string, ClubPalette> = {
  // === BIG 6 ===
  arsenal: {
    primary: '#EF0107',
    secondary: '#023474',
    accent: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #EF0107 0%, #9C0004 50%, #023474 100%)',
    glowColor: 'rgba(239, 1, 7, 0.12)',
    textOnPrimary: '#FFFFFF',
  },
  chelsea: {
    primary: '#034694',
    secondary: '#DBA111',
    accent: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #034694 0%, #001489 50%, #DBA111 100%)',
    glowColor: 'rgba(3, 70, 148, 0.12)',
    textOnPrimary: '#FFFFFF',
  },
  liverpool: {
    primary: '#C8102E',
    secondary: '#00B2A9',
    accent: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #C8102E 0%, #8B0000 50%, #00B2A9 100%)',
    glowColor: 'rgba(200, 16, 46, 0.12)',
    textOnPrimary: '#FFFFFF',
  },
  manchester_united: {
    primary: '#DA291C',
    secondary: '#FBE122',
    accent: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #DA291C 0%, #8B0000 50%, #FBE122 100%)',
    glowColor: 'rgba(218, 41, 28, 0.12)',
    textOnPrimary: '#FFFFFF',
  },
  manchester_city: {
    primary: '#6CABDD',
    secondary: '#1C2C5B',
    accent: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #6CABDD 0%, #1C2C5B 100%)',
    glowColor: 'rgba(108, 171, 221, 0.12)',
    textOnPrimary: '#1C2C5B',
  },
  tottenham: {
    primary: '#132257',
    secondary: '#FFFFFF',
    accent: '#132257',
    gradient: 'linear-gradient(135deg, #132257 0%, #0B1432 50%, #FFFFFF 100%)',
    glowColor: 'rgba(19, 34, 87, 0.15)',
    textOnPrimary: '#FFFFFF',
  },

  // === ESTABLISHED ===
  newcastle: {
    primary: '#241F20',
    secondary: '#FFFFFF',
    accent: '#41B6E6',
    gradient: 'linear-gradient(135deg, #241F20 0%, #41B6E6 100%)',
    glowColor: 'rgba(65, 182, 230, 0.10)',
    textOnPrimary: '#FFFFFF',
  },
  west_ham: {
    primary: '#7A263A',
    secondary: '#1BB1E7',
    accent: '#F3D459',
    gradient: 'linear-gradient(135deg, #7A263A 0%, #1BB1E7 100%)',
    glowColor: 'rgba(122, 38, 58, 0.12)',
    textOnPrimary: '#FFFFFF',
  },
  everton: {
    primary: '#003399',
    secondary: '#FFFFFF',
    accent: '#003399',
    gradient: 'linear-gradient(135deg, #003399 0%, #001A4E 100%)',
    glowColor: 'rgba(0, 51, 153, 0.12)',
    textOnPrimary: '#FFFFFF',
  },
  aston_villa: {
    primary: '#670E36',
    secondary: '#95BFE5',
    accent: '#FEE505',
    gradient: 'linear-gradient(135deg, #670E36 0%, #95BFE5 100%)',
    glowColor: 'rgba(103, 14, 54, 0.12)',
    textOnPrimary: '#FFFFFF',
  },

  // === MID-TABLE ===
  brighton: {
    primary: '#0057B8',
    secondary: '#FFFFFF',
    accent: '#FFCD00',
    gradient: 'linear-gradient(135deg, #0057B8 0%, #003C7A 100%)',
    glowColor: 'rgba(0, 87, 184, 0.12)',
    textOnPrimary: '#FFFFFF',
  },
  wolves: {
    primary: '#FDB913',
    secondary: '#231F20',
    accent: '#FDB913',
    gradient: 'linear-gradient(135deg, #FDB913 0%, #231F20 100%)',
    glowColor: 'rgba(253, 185, 19, 0.10)',
    textOnPrimary: '#231F20',
  },
  crystal_palace: {
    primary: '#1B458F',
    secondary: '#C4122E',
    accent: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #1B458F 0%, #C4122E 100%)',
    glowColor: 'rgba(27, 69, 143, 0.12)',
    textOnPrimary: '#FFFFFF',
  },
  fulham: {
    primary: '#CC0000',
    secondary: '#000000',
    accent: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #000000 0%, #CC0000 100%)',
    glowColor: 'rgba(204, 0, 0, 0.10)',
    textOnPrimary: '#FFFFFF',
  },
  nottingham_forest: {
    primary: '#DD0000',
    secondary: '#FFFFFF',
    accent: '#DD0000',
    gradient: 'linear-gradient(135deg, #DD0000 0%, #8B0000 100%)',
    glowColor: 'rgba(221, 0, 0, 0.12)',
    textOnPrimary: '#FFFFFF',
  },
  brentford: {
    primary: '#E30613',
    secondary: '#FBB800',
    accent: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #E30613 0%, #FBB800 100%)',
    glowColor: 'rgba(227, 6, 19, 0.12)',
    textOnPrimary: '#FFFFFF',
  },
  bournemouth: {
    primary: '#DA291C',
    secondary: '#000000',
    accent: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #DA291C 0%, #000000 100%)',
    glowColor: 'rgba(218, 41, 28, 0.10)',
    textOnPrimary: '#FFFFFF',
  },

  // === PROMOTED / RETURNING ===
  sunderland: {
    primary: '#EB172B',
    secondary: '#FFFFFF',
    accent: '#211E1F',
    gradient: 'linear-gradient(135deg, #EB172B 0%, #211E1F 100%)',
    glowColor: 'rgba(235, 23, 43, 0.12)',
    textOnPrimary: '#FFFFFF',
  },
  leeds: {
    primary: '#FFCD00',
    secondary: '#1D428A',
    accent: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #1D428A 0%, #FFCD00 100%)',
    glowColor: 'rgba(255, 205, 0, 0.10)',
    textOnPrimary: '#1D428A',
  },
  burnley: {
    primary: '#6C1D45',
    secondary: '#99D6EA',
    accent: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #6C1D45 0%, #99D6EA 100%)',
    glowColor: 'rgba(108, 29, 69, 0.12)',
    textOnPrimary: '#FFFFFF',
  },

  // === LEGACY (may not be in current PL) ===
  ipswich: {
    primary: '#0044AA',
    secondary: '#FFFFFF',
    accent: '#0044AA',
    gradient: 'linear-gradient(135deg, #0044AA 0%, #002266 100%)',
    glowColor: 'rgba(0, 68, 170, 0.12)',
    textOnPrimary: '#FFFFFF',
  },
  southampton: {
    primary: '#D71920',
    secondary: '#130C0E',
    accent: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #D71920 0%, #130C0E 100%)',
    glowColor: 'rgba(215, 25, 32, 0.12)',
    textOnPrimary: '#FFFFFF',
  },
  leicester: {
    primary: '#003090',
    secondary: '#FDBE11',
    accent: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #003090 0%, #FDBE11 100%)',
    glowColor: 'rgba(0, 48, 144, 0.12)',
    textOnPrimary: '#FFFFFF',
  },
}

/** Neutral analyst palette — editorial monochrome */
export const ANALYST_PALETTE: ClubPalette = {
  primary: '#94A3B8',
  secondary: '#475569',
  accent: '#E2E8F0',
  gradient: 'linear-gradient(135deg, #1E293B 0%, #0F172A 100%)',
  glowColor: 'rgba(148, 163, 184, 0.06)',
  textOnPrimary: '#FFFFFF',
}

/** Default palette when no club selected */
export const DEFAULT_PALETTE: ClubPalette = {
  primary: '#10B981',
  secondary: '#3B82F6',
  accent: '#FFFFFF',
  gradient: 'linear-gradient(135deg, #10B981 0%, #3B82F6 100%)',
  glowColor: 'rgba(16, 185, 129, 0.08)',
  textOnPrimary: '#FFFFFF',
}

export function getClubPalette(clubId: string | null): ClubPalette {
  if (!clubId) return DEFAULT_PALETTE
  if (clubId === 'analyst') return ANALYST_PALETTE
  return CLUB_PALETTES[clubId] || DEFAULT_PALETTE
}
