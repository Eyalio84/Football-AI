/**
 * Soccer-AI Flask Frontend JavaScript
 * Handles API communication with FastAPI backend on port 8000
 */

const API_BASE = 'http://localhost:8000';

// API helper
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Export for use in templates
window.SoccerAI = {
    apiCall,
    API_BASE
};
