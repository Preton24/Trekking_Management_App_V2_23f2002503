// One small wrapper around fetch() so every page talks to the backend the same way.
// It adds the base URL, sends/reads JSON, attaches the JWT, and logs the user out
// when the backend says the token is no longer valid (401).
import { API_BASE_URL } from '@/config.js'
import { auth, clearLogin } from '@/auth.js'

// Usage:  const data = await apiFetch('/api/treks')
//         await apiFetch('/api/auth/login', { method: 'POST', body: {...}, auth: false })
// Returns the parsed JSON. Throws an Error whose message is safe to show to the user.
export async function apiFetch(path, options = {}) {
  const method = options.method || 'GET'
  const useToken = options.auth !== false // login/register have no token to send

  const headers = {}
  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }
  if (useToken && auth.token) {
    // This is the header the Flask JWT code reads
    headers['Authorization'] = 'Bearer ' + auth.token
  }

  let response
  try {
    response = await fetch(API_BASE_URL + path, {
      method: method,
      headers: headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    })
  } catch (networkError) {
    // fetch() only throws when the server cannot be reached at all
    throw new Error('Cannot reach the server. Please check that the backend is running.')
  }

  // Some responses may have no JSON body, so fall back to an empty object
  let data = {}
  try {
    data = await response.json()
  } catch (parseError) {
    data = {}
  }

  if (response.status === 401 && useToken) {
    // Token missing, expired or invalid: forget it and go to the login page.
    // A full page load is used (instead of the router) so this file does not
    // need to import the router, which would create a circular import.
    clearLogin()
    window.location.href = '/login'
    throw new Error(data.error || 'Your session has expired. Please log in again.')
  }

  if (!response.ok) {
    // Our backend always replies { "error": "..." } on failure
    throw new Error(data.error || 'Something went wrong (status ' + response.status + ').')
  }

  return data
}
