/**
 * Configuration de l'API
 */

// URL de l'API backend - peut être configurée via variable d'environnement
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

// Timeout par défaut pour les requêtes (30 secondes)
export const API_TIMEOUT = 30000;

// Clés de stockage localStorage
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token', // Pour usage futur
} as const;

