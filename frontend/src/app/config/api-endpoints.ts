export const API_ENDPOINTS = {
  admins: '/api/admins',
  alerts: '/api/alerts',
  auth: {
    login: '/api/auth/login',
    logout: '/api/auth/logout',
    me: '/api/auth/me',
    register: '/api/auth/register'
  },
  health: '/api/health',
  hospitals: '/api/hospitals',
  sessions: '/api/sessions',
  shifts: '/api/shifts',
  timeoff: '/api/timeoff',
  users: '/api/users'
} as const;

/**
 * Helper function to build full API URL
 */
export function buildApiUrl(endpoint: string, baseUrl: string): string {
  return `${baseUrl}${endpoint}`;
}
