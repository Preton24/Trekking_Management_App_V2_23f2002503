// Keeps the logged-in user's details (token, role, name).
// They are saved in localStorage so a page refresh does not log the user out,
// and also held in a Vue `reactive` object so components such as the Navbar
// update on their own the moment someone logs in or out.
import { reactive } from 'vue'

export const auth = reactive({
  token: localStorage.getItem('token'),
  role: localStorage.getItem('role'),
  name: localStorage.getItem('name'),
})

// Called after a successful login: store what the backend sent us
export function saveLogin(data) {
  auth.token = data.access_token
  auth.role = data.role
  auth.name = data.name
  localStorage.setItem('token', data.access_token)
  localStorage.setItem('role', data.role)
  localStorage.setItem('name', data.name)
}

// Forget the user completely (logout, or the token was rejected)
export function clearLogin() {
  auth.token = null
  auth.role = null
  auth.name = null
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  localStorage.removeItem('name')
}

// Each role has its own home page after login
export function dashboardPath(role) {
  if (role === 'admin') return '/admin'
  if (role === 'staff') return '/staff'
  if (role === 'trekker') return '/trekker'
  return '/login'
}

// Used by the Profile page after the name is changed, so the navbar shows the new name
export function updateName(name) {
  auth.name = name
  localStorage.setItem('name', name)
}
