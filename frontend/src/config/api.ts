/**
 * API Configuration
 *
 * Single source of truth for the backend API URL.
 * Uses VITE_API_URL env var in production, falls back to localhost for dev.
 */

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
