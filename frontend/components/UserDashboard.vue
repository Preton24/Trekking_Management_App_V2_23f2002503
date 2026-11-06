<template>
  <div class="container py-4">
    <h1 class="h3">Welcome, {{ auth.name }}</h1>
    <p class="text-muted">Find your next trek.</p>

    <div v-if="loading" class="text-muted">Loading...</div>

    <div v-else>
      <!-- Summary numbers -->
      <div class="row g-3 mb-4">
        <div v-for="card in cards" :key="card.label" class="col-12 col-sm-4">
          <div class="card shadow-sm h-100">
            <div class="card-body">
              <div class="text-muted small">{{ card.label }}</div>
              <div class="display-6">{{ card.value }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Available treks: show the first three, the rest are on the browse page -->
      <div class="d-flex justify-content-between align-items-center mb-2">
        <h2 class="h5 mb-0">Available treks</h2>
        <router-link to="/trekker/browse">View all</router-link>
      </div>
      <p v-if="treks.length === 0" class="text-muted">No treks are open for booking right now.</p>
      <div class="row g-3 mb-4">
        <div v-for="trek in treks.slice(0, 3)" :key="trek.id" class="col-12 col-md-6 col-lg-4">
          <TrekCard :trek="trek" />
        </div>
      </div>

      <!-- Booked treks and their status -->
      <div class="d-flex justify-content-between align-items-center mb-2">
        <h2 class="h5 mb-0">My bookings</h2>
        <router-link to="/trekker/bookings">View all</router-link>
      </div>
      <p v-if="bookings.length === 0" class="text-muted">You have not booked any trek yet.</p>
      <div v-else class="table-responsive">
        <table class="table align-middle">
          <thead class="table-light">
            <tr><th>Trek</th><th>Starts</th><th>Status</th></tr>
          </thead>
          <tbody>
            <tr v-for="booking in bookings.slice(0, 5)" :key="booking.id">
              <td>{{ booking.trek_name }}</td>
              <td>{{ booking.start_date }}</td>
              <td><span class="badge" :class="statusBadge(booking.status)">{{ booking.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import TrekCard from '@components/TrekCard.vue'
import { apiFetch } from '@/api.js'
import { auth } from '@/auth.js'
import { showToast } from '@/toast.js'
import { bookingStatusBadge } from '@/ui.js'

export default {
  name: 'UserDashboard',
  components: { TrekCard },
  data() {
    return { auth: auth, treks: [], bookings: [], loading: true }
  },
  computed: {
    cards() {
      const active = this.bookings.filter((b) => b.status === 'Booked').length
      const completed = this.bookings.filter((b) => b.status === 'Completed').length
      return [
        { label: 'Treks open for booking', value: this.treks.length },
        { label: 'My upcoming bookings', value: active },
        { label: 'Treks completed', value: completed },
      ]
    },
  },
  async mounted() {
    try {
      const [treks, bookings] = await Promise.all([apiFetch('/api/treks'), apiFetch('/api/bookings/me')])
      this.treks = treks
      this.bookings = bookings
    } catch (err) {
      showToast(err.message, 'danger')
    } finally {
      this.loading = false
    }
  },
  methods: { statusBadge: bookingStatusBadge },
}
</script>
