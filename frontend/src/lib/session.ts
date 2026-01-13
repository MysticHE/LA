/**
 * Session ID management for secure per-browser isolation.
 *
 * Each browser gets a unique session ID stored in localStorage,
 * ensuring API keys are isolated between users/browsers.
 */

const SESSION_ID_KEY = 'linkedin_content_session_id'

/**
 * Get or create a unique session ID for this browser.
 * Uses crypto.randomUUID() for cryptographically secure IDs.
 */
export function getSessionId(): string {
  // Check localStorage first
  let sessionId = localStorage.getItem(SESSION_ID_KEY)

  if (!sessionId) {
    // Generate new UUID
    sessionId = crypto.randomUUID()
    localStorage.setItem(SESSION_ID_KEY, sessionId)
  }

  return sessionId
}

/**
 * Clear the session ID (e.g., on logout or disconnect all).
 * Next call to getSessionId() will generate a new ID.
 */
export function clearSessionId(): void {
  localStorage.removeItem(SESSION_ID_KEY)
}

/**
 * Check if a session ID exists.
 */
export function hasSessionId(): boolean {
  return localStorage.getItem(SESSION_ID_KEY) !== null
}
