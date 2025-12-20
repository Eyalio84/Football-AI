import { Club, Game, Standing, Prediction } from '../types';

export const MOCK_CLUBS: Club[] = [
  { id: 'arsenal', name: 'Arsenal' },
  { id: 'chelsea', name: 'Chelsea' },
  { id: 'liverpool', name: 'Liverpool' },
  { id: 'manchester_united', name: 'Manchester United' },
  { id: 'manchester_city', name: 'Manchester City' },
  { id: 'tottenham', name: 'Tottenham' },
  { id: 'newcastle', name: 'Newcastle United' },
  { id: 'west_ham', name: 'West Ham United' },
  { id: 'everton', name: 'Everton' },
  { id: 'brighton', name: 'Brighton & Hove Albion' },
  { id: 'aston_villa', name: 'Aston Villa' },
  { id: 'wolves', name: 'Wolverhampton Wanderers' },
  { id: 'crystal_palace', name: 'Crystal Palace' },
  { id: 'fulham', name: 'Fulham' },
  { id: 'nottingham_forest', name: 'Nottingham Forest' },
  { id: 'brentford', name: 'Brentford' },
  { id: 'bournemouth', name: 'AFC Bournemouth' },
  { id: 'leicester', name: 'Leicester City' },
  { id: 'ipswich', name: 'Ipswich Town' },
  { id: 'southampton', name: 'Southampton' },
  { id: 'analyst', name: 'Neutral Analyst' }
];

export const MOCK_STANDINGS: Standing[] = [
  { position: 1, team_id: 4, team_name: 'Liverpool', short_name: 'LIV', played: 17, won: 14, drawn: 2, lost: 1, goals_for: 45, goals_against: 15, goal_difference: 30, points: 44, form: 'WWDWW' },
  { position: 2, team_id: 5, team_name: 'Chelsea', short_name: 'CHE', played: 17, won: 10, drawn: 4, lost: 3, goals_for: 38, goals_against: 20, goal_difference: 18, points: 34, form: 'DWWLW' },
  { position: 3, team_id: 1, team_name: 'Arsenal', short_name: 'ARS', played: 17, won: 9, drawn: 5, lost: 3, goals_for: 32, goals_against: 18, goal_difference: 14, points: 32, form: 'WDWDW' },
  { position: 4, team_id: 3, team_name: 'Nottingham Forest', short_name: 'NFO', played: 17, won: 9, drawn: 4, lost: 4, goals_for: 25, goals_against: 19, goal_difference: 6, points: 31, form: 'LWWDW' },
  { position: 5, team_id: 6, team_name: 'Manchester City', short_name: 'MCI', played: 17, won: 8, drawn: 4, lost: 5, goals_for: 32, goals_against: 24, goal_difference: 8, points: 28, form: 'LLWDL' },
  { position: 6, team_id: 9, team_name: 'Aston Villa', short_name: 'AVL', played: 17, won: 8, drawn: 3, lost: 6, goals_for: 25, goals_against: 25, goal_difference: 0, points: 27, form: 'WLDWL' },
  { position: 7, team_id: 7, team_name: 'Tottenham', short_name: 'TOT', played: 17, won: 8, drawn: 1, lost: 8, goals_for: 35, goals_against: 26, goal_difference: 9, points: 25, form: 'LWLDW' },
  { position: 18, team_id: 18, team_name: 'Leicester City', short_name: 'LEI', played: 17, won: 4, drawn: 4, lost: 9, goals_for: 22, goals_against: 37, goal_difference: -15, points: 16, form: 'LLLDW' },
  { position: 19, team_id: 19, team_name: 'Ipswich Town', short_name: 'IPS', played: 17, won: 2, drawn: 7, lost: 8, goals_for: 16, goals_against: 31, goal_difference: -15, points: 13, form: 'DLLDD' },
  { position: 20, team_id: 20, team_name: 'Southampton', short_name: 'SOU', played: 17, won: 1, drawn: 3, lost: 13, goals_for: 11, goals_against: 37, goal_difference: -26, points: 6, form: 'LLLLD' }
];

export const MOCK_FIXTURES: Game[] = [
  { id: 1, date: '2024-12-21', time: '15:00', status: 'finished', home_team_id: 1, home_team_name: 'Arsenal', home_team_short: 'ARS', away_team_id: 5, away_team_name: 'Chelsea', away_team_short: 'CHE', home_score: 2, away_score: 1, competition: 'Premier League', venue: 'Emirates Stadium' },
  { id: 2, date: '2024-12-21', time: '17:30', status: 'live', home_team_id: 4, home_team_name: 'Liverpool', home_team_short: 'LIV', away_team_id: 6, away_team_name: 'Manchester City', away_team_short: 'MCI', home_score: 1, away_score: 1, competition: 'Premier League', venue: 'Anfield' },
  { id: 3, date: '2024-12-22', time: '14:00', status: 'scheduled', home_team_id: 2, home_team_name: 'Manchester United', home_team_short: 'MUN', away_team_id: 7, away_team_name: 'Tottenham', away_team_short: 'TOT', competition: 'Premier League', venue: 'Old Trafford' },
  { id: 4, date: '2024-12-22', time: '16:30', status: 'scheduled', home_team_id: 12, home_team_name: 'Wolves', home_team_short: 'WOL', away_team_id: 11, away_team_name: 'Aston Villa', away_team_short: 'AVL', competition: 'Premier League', venue: 'Molineux' }
];

export const MOCK_CHAT_RESPONSES: Record<string, string> = {
  arsenal: "Ah mate, what a time to be a Gooner! Saka's been absolutely brilliant lately. Remember when people doubted Arteta? Look at us now - the process is real! COYG!",
  chelsea: "Blues through and through! The gaffer's got us playing some proper football again. That youth academy is churning out gems - Cobham's finest!",
  liverpool: "You'll Never Walk Alone, mate! The Kop's been bouncing this season. Remember Istanbul? That's the spirit that runs through this club!",
  manchester_united: "Glory Glory Man United! The Theater of Dreams is where legends are made. We've had our ups and downs, but the class is permanent.",
  manchester_city: "Blue Moon rising! Pep's mastermind tactics are just on another level. We don't just win matches, we dominate the pitch.",
  tottenham: "To Dare Is To Do! The atmosphere at the new stadium is absolutely electric. We're playing some proper attacking football now.",
  analyst: "Looking at the tactical setup, the pressing patterns have been particularly effective this season. The expected goals model suggests some regression to the mean is likely."
};

export const MOCK_PREDICTION: Prediction = {
  home_team: 'Arsenal',
  away_team: 'Man City',
  favorite: 'Arsenal',
  underdog: 'Man City',
  side_a_score: 65,
  side_b_score: 45,
  base_upset_prob: 0.28,
  pattern_multiplier: 1.15,
  final_upset_prob: 0.32,
  patterns_triggered: [
    { name: 'derby_caution', multiplier: 1.15, confidence: 0.8 },
    { name: 'top_vs_top', multiplier: 1.05, confidence: 0.9 }
  ],
  confidence_level: 'medium',
  key_insight: 'Historic rivalry adds unpredictability, but Arsenal\'s home form gives them the edge.'
};