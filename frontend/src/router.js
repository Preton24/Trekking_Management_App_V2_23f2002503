import { createRouter, createWebHistory } from 'vue-router'
import { auth, dashboardPath } from '@/auth.js'

// Page components live in frontend/components/ (outside src/), imported via the alias
import Login from '@components/Login.vue'
import Register from '@components/Register.vue'
import AdminDashboard from '@components/AdminDashboard.vue'
import StaffDashboard from '@components/StaffDashboard.vue'
import UserDashboard from '@components/UserDashboard.vue'
import TrekBrowse from '@components/TrekBrowse.vue'
import TrekDetail from '@components/TrekDetail.vue'
import BookingHistory from '@components/BookingHistory.vue'
import Profile from '@components/Profile.vue'
import TrekManagement from '@components/TrekManagement.vue'
import StaffManagement from '@components/StaffManagement.vue'
import UserManagement from '@components/UserManagement.vue'
import AllBookings from '@components/AllBookings.vue'
import AdminSearch from '@components/AdminSearch.vue'

// meta.public = anyone may open it (and logged-in users are sent to their dashboard)
// meta.role   = only that role may open it
const routes = [
  // "/" has no page of its own: send people to the right place
  { path: '/', redirect: () => (auth.token ? dashboardPath(auth.role) : '/login') },
  { path: '/login', name: 'login', component: Login, meta: { public: true } },
  { path: '/register', name: 'register', component: Register, meta: { public: true } },
  { path: '/admin', name: 'admin-dashboard', component: AdminDashboard, meta: { role: 'admin' } },
  { path: '/admin/treks', name: 'admin-treks', component: TrekManagement, meta: { role: 'admin' } },
  { path: '/admin/staff', name: 'admin-staff', component: StaffManagement, meta: { role: 'admin' } },
  { path: '/admin/users', name: 'admin-users', component: UserManagement, meta: { role: 'admin' } },
  { path: '/admin/bookings', name: 'admin-bookings', component: AllBookings, meta: { role: 'admin' } },
  { path: '/admin/search', name: 'admin-search', component: AdminSearch, meta: { role: 'admin' } },
  { path: '/staff', name: 'staff-dashboard', component: StaffDashboard, meta: { role: 'staff' } },
  { path: '/trekker', name: 'trekker-dashboard', component: UserDashboard, meta: { role: 'trekker' } },
  { path: '/trekker/browse', name: 'trekker-browse', component: TrekBrowse, meta: { role: 'trekker' } },
  // :id is the trek id; TrekDetail reads it from $route.params.id
  { path: '/trekker/treks/:id', name: 'trekker-trek', component: TrekDetail, meta: { role: 'trekker' } },
  { path: '/trekker/bookings', name: 'trekker-bookings', component: BookingHistory, meta: { role: 'trekker' } },
  { path: '/trekker/profile', name: 'trekker-profile', component: Profile, meta: { role: 'trekker' } },
  // Any unknown URL goes back to "/"
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Route guard: runs before every page change.
// NOTE: this only improves the experience. Real security is the role check
// on every backend route, because anyone can edit localStorage in the browser.
router.beforeEach((to) => {
  const loggedIn = !!auth.token

  // Public pages (login/register): a logged-in user has no need for them
  if (to.meta.public) {
    return loggedIn ? dashboardPath(auth.role) : true
  }

  // Everything else needs a login
  if (!loggedIn) {
    return '/login'
  }

  // Logged in, but trying to open another role's page: send them to their own
  if (to.meta.role && to.meta.role !== auth.role) {
    return dashboardPath(auth.role)
  }

  return true
})

export default router
