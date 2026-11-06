<template>
  <nav class="navbar navbar-expand-md navbar-dark bg-success">
    <div class="container">
      <router-link class="navbar-brand fw-bold" to="/">Trekking Management</router-link>

      <!-- Hamburger button, only visible on small screens -->
      <button
        class="navbar-toggler"
        type="button"
        aria-label="Toggle navigation"
        :aria-expanded="menuOpen"
        @click="menuOpen = !menuOpen"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <!-- On mobile this block is hidden until the hamburger is tapped ("show" class) -->
      <div class="navbar-collapse collapse" :class="{ show: menuOpen }">
        <ul class="navbar-nav me-auto mb-2 mb-md-0">
          <!-- Links depend on the role (see the `links` computed property below) -->
          <li v-for="link in links" :key="link.to" class="nav-item">
            <router-link class="nav-link" :to="link.to" exact-active-class="active" @click="menuOpen = false">
              {{ link.label }}
            </router-link>
          </li>
        </ul>

        <!-- Global search, admin only -->
        <SearchBar v-if="auth.role === 'admin'" class="mb-2 mb-md-0 me-md-3" @searched="menuOpen = false" />

        <!-- Logged in: show the name, the role and a Logout button -->
        <div v-if="auth.token" class="d-flex flex-column flex-md-row align-items-md-center gap-2">
          <span class="navbar-text text-white">
            {{ auth.name }}
            <span class="badge bg-light text-success text-capitalize">{{ auth.role }}</span>
          </span>
          <button class="btn btn-outline-light btn-sm" type="button" @click="logout">Logout</button>
        </div>

        <!-- Logged out: show Login and Register -->
        <div v-else class="d-flex flex-column flex-md-row gap-2">
          <router-link class="btn btn-outline-light btn-sm" to="/login" @click="menuOpen = false">Login</router-link>
          <router-link class="btn btn-light btn-sm" to="/register" @click="menuOpen = false">Register</router-link>
        </div>
      </div>
    </div>
  </nav>
</template>

<script>
import SearchBar from '@components/SearchBar.vue'
import { auth, clearLogin, dashboardPath } from '@/auth.js'

export default {
  name: 'Navbar',
  components: { SearchBar },
  data() {
    return {
      auth: auth, // reactive, so the navbar redraws when the user logs in or out
      menuOpen: false, // whether the mobile menu is expanded
    }
  },
  computed: {
    // Only links to pages that exist. Each role only sees links to its own pages.
    links() {
      if (!auth.token) {
        return []
      }
      if (auth.role === 'admin') {
        return [
          { label: 'Dashboard', to: '/admin' },
          { label: 'Treks', to: '/admin/treks' },
          { label: 'Staff', to: '/admin/staff' },
          { label: 'Users', to: '/admin/users' },
          { label: 'Bookings', to: '/admin/bookings' },
        ]
      }
      if (auth.role === 'trekker') {
        return [
          { label: 'Dashboard', to: '/trekker' },
          { label: 'Browse treks', to: '/trekker/browse' },
          { label: 'My bookings', to: '/trekker/bookings' },
          { label: 'Profile', to: '/trekker/profile' },
        ]
      }
      // Staff manage everything from their dashboard
      return [{ label: 'Dashboard', to: dashboardPath(auth.role) }]
    },
  },
  methods: {
    logout() {
      this.menuOpen = false
      clearLogin()
      this.$router.push('/login')
    },
  },
}
</script>
