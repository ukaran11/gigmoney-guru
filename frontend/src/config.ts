/// <reference types="vite/client" />

// API Configuration
// Automatically switches between local and production based on environment
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
