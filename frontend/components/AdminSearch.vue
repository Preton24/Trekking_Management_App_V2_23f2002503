<template>
  <div class="container py-4">
    <h1 class="h3">Search results</h1>
    <p class="text-muted">Showing matches for "{{ query }}"</p>

    <div v-if="loading" class="text-muted">Searching...</div>

    <div v-else>
      <h2 class="h5 mt-4">Treks ({{ treks.length }})</h2>
      <p v-if="treks.length === 0" class="text-muted">No treks found.</p>
      <ul v-else class="list-group mb-3">
        <li v-for="trek in treks" :key="trek.id" class="list-group-item d-flex justify-content-between align-items-center">
          <span>{{ trek.name }} <span class="text-muted small">- {{ trek.location }}</span></span>
          <span class="badge" :class="statusBadge(trek.status)">{{ trek.status }}</span>
        </li>
      </ul>

      <h2 class="h5 mt-4">Trekkers ({{ users.length }})</h2>
      <p v-if="users.length === 0" class="text-muted">No trekkers found.</p>
      <ul v-else class="list-group mb-3">
        <li v-for="user in users" :key="user.id" class="list-group-item d-flex justify-content-between align-items-center">
          <span>{{ user.name }} <span class="text-muted small">- {{ user.email }}</span></span>
          <span v-if="user.is_blacklisted" class="badge bg-danger">Blacklisted</span>
        </li>
      </ul>

      <h2 class="h5 mt-4">Staff ({{ staff.length }})</h2>
      <p v-if="staff.length === 0" class="text-muted">No staff found.</p>
      <ul v-else class="list-group mb-3">
        <li v-for="person in staff" :key="person.id" class="list-group-item d-flex justify-content-between align-items-center">
          <span>{{ person.name }} <span class="text-muted small">- {{ person.email }}</span></span>
          <span v-if="person.is_blacklisted" class="badge bg-danger">Blacklisted</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { apiFetch } from '@/api.js'
import { showToast } from '@/toast.js'
import { trekStatusBadge } from '@/ui.js'

export default {
  name: 'AdminSearch',
  data() {
    return { treks: [], users: [], staff: [], loading: false }
  },
  computed: {
    query() {
      return this.$route.query.q || ''
    },
  },
  watch: {
    // The search bar stays in the navbar, so a new search changes the URL without remounting this page
    query() {
      this.search()
    },
  },
  mounted() {
    this.search()
  },
  methods: {
    statusBadge: trekStatusBadge,

    async search() {
      if (!this.query) {
        return
      }
      this.loading = true
      const q = encodeURIComponent(this.query)
      try {
        // The backend searches one type at a time, so ask for all three together
        const [treks, users, staff] = await Promise.all([
          apiFetch('/api/admin/search?type=treks&q=' + q),
          apiFetch('/api/admin/search?type=users&q=' + q),
          apiFetch('/api/admin/search?type=staff&q=' + q),
        ])
        this.treks = treks
        this.users = users
        this.staff = staff
      } catch (err) {
        showToast(err.message, 'danger')
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
