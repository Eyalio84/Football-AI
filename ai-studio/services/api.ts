import { ApiResponse, ChatResponse, Club, Game, Prediction, Standing } from '../types';
import { MOCK_CHAT_RESPONSES, MOCK_CLUBS, MOCK_FIXTURES, MOCK_PREDICTION, MOCK_STANDINGS } from '../constants/mock-data';

const API_BASE = 'http://localhost:8000/api/v1';
const USE_MOCK_DATA = true; // Toggle to false when backend is running

// Helper to simulate network delay for mock data
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const api = {
  // Chat with club persona
  chat: async (message: string, club?: string, conversationId?: string): Promise<ApiResponse<ChatResponse>> => {
    if (USE_MOCK_DATA) {
      await delay(800 + Math.random() * 1000); // Simulate "thinking"
      return {
        success: true,
        data: {
          response: MOCK_CHAT_RESPONSES[club || 'analyst'] || MOCK_CHAT_RESPONSES.analyst,
          conversation_id: conversationId || crypto.randomUUID(),
          sources: [{ type: 'persona' }],
          confidence: 0.85
        }
      };
    }
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, club, conversation_id: conversationId })
    });
    return res.json();
  },

  // Get all clubs for persona selection
  getClubs: async (): Promise<ApiResponse<Club[]>> => {
    if (USE_MOCK_DATA) {
      await delay(200);
      return { success: true, data: MOCK_CLUBS };
    }
    const res = await fetch(`${API_BASE}/clubs`);
    return res.json();
  },

  // Get today's fixtures
  getFixturesToday: async (): Promise<ApiResponse<Game[]>> => {
    if (USE_MOCK_DATA) {
      await delay(400);
      // Filter fixtures that look like they are "today" (using mock logic)
      const today = new Date().toISOString().split('T')[0];
      // For mock purposes, just return a subset or all
      return { success: true, data: MOCK_FIXTURES.slice(0, 2) };
    }
    const res = await fetch(`${API_BASE}/games/today`);
    return res.json();
  },

  // Get upcoming fixtures
  getFixturesUpcoming: async (): Promise<ApiResponse<Game[]>> => {
    if (USE_MOCK_DATA) {
      await delay(400);
      return { success: true, data: MOCK_FIXTURES };
    }
    const res = await fetch(`${API_BASE}/games/upcoming`);
    return res.json();
  },

  // Get standings
  getStandings: async (league: string = 'premier-league'): Promise<ApiResponse<Standing[]>> => {
    if (USE_MOCK_DATA) {
      await delay(500);
      return { success: true, data: MOCK_STANDINGS };
    }
    const res = await fetch(`${API_BASE}/standings/${league}`);
    return res.json();
  },

  // Get match prediction
  getPrediction: async (homeTeam: string, awayTeam: string): Promise<ApiResponse<Prediction>> => {
    if (USE_MOCK_DATA) {
      await delay(1200); // Analysis takes time
      return {
        success: true,
        data: {
            ...MOCK_PREDICTION,
            home_team: homeTeam,
            away_team: awayTeam,
            favorite: homeTeam
        }
      };
    }
    const res = await fetch(`${API_BASE}/predict?home_team=${encodeURIComponent(homeTeam)}&away_team=${encodeURIComponent(awayTeam)}`, {
      method: 'POST'
    });
    return res.json();
  }
};