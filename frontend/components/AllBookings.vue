<template>
  <div class="container py-4">
    <h1 class="h3 mb-3">All bookings</h1>

    <!-- Filters: changing any of them reloads the list from the backend -->
    <div class="row g-2 mb-3">
      <div class="col-12 col-md-4">
        <select v-model="trekId" class="form-select" aria-label="Filter by trek" @change="load">
          <option value="">All treks</option>
          <option v-for="trek in treks" :key="trek.id" :value="trek.id">{{ trek.name }}</option>
        </select>
      </div>
      <div class="col-12 col-md-4">
        <select v-model="userId" class="form-select" aria-label="Filter by trekker" @change="load">
          <option value="">All trekkers</option>
          <option v-for="user in users" :key="user.id" :value="user.id">{{ user.name }}</option>
        </select>
      </div>
      <div class="col-8 col-md-3">
        <select v-model="status" class="form-select" aria-label="Filter by status" @change="load">
          <option value="">All statuses</option>
          <option>Booked</option>
          <option>Completed</option>
          <option>Cancelled</option>
        </select>
      </div>
      <div class="col-4 col-md-1">
        <button class="btn btn-outline-secondary w-100" type="button" @click="clearFilters">Clear</button>
      </div>
    </div>

    <div v-if="loading" class="text-muted">Loading bookings...</div>
    <div v-else-if="bookings.length === 0" class="alert alert-secondary">No bookings match these filters.</div>

    <div v-else>
      <p class="text-muted small">{{ bookings.length }} booking(s), newest first</p>
      <div class="table-responsive">
        <table class="table table-hover align-middle">
          <thead class="table-light">
            <tr><th>ID</th><th>Trekker</th><th>Trek</th><th>Booked on</th><th>Status</th><th>Payment</th></tr>
          </thead>
          <tbody>
            <tr v-for="booking in bookings" :key="booking.id">
              <td>#{{ booking.id }}</td>
              <td>{{ booking.user_name }}</td>
              <td>{{ booking.trek_name }}</td>
              <td>{{ shortDate(booking.booking_date) }}</td>
              <td><span class="badge" :class="statusBadge(booking.status)">{{ booking.status }}</span></td>
              <td>{{ booking.payment_status }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { apiFetch } from '@/api.js'
import { showToast } from '@/toast.js'
import { bookingStatusBadge, shortDate } from '@/ui.js'

export default {
  name: 'AllBookings',
  data() {
    return { bookings: [], treks: [], users: [], trekId: '', userId: '', status: '', loading: true }
  },
  async mounted() {
    // Fill the two filter dropdowns first, then load the bookings
    try {
      const [treks, users] = await Promise.all([
        apiFetch('/api/admin/treks'),
        apiFetch('/api/admin/users'),
      ])
      this.treks = treks
      this.users = users
    } catch (err) {
      showToast(err.message, 'danger')
    }
    this.load()
  },
  methods: {
    statusBadge: bookingStatusBadge,
    shortDate: shortDate,

    async load() {
      // Only filters that have a value are added to the URL
      const params = new URLSearchParams()
      if (this.trekId) params.append('trek_id', this.trekId)
      if (this.userId) params.append('user_id', this.userId)
      if (this.status) params.append('status', this.status)

      try {
        this.bookings = await apiFetch('/api/admin/bookings?' + params.toString())
      } catch (err) {
        showToast(err.message, 'danger')
      } finally {
        this.loading = false
      }
    },
    clearFilters() {
      this.trekId = ''
      this.userId = ''
      this.status = ''
      this.load()
    },
  },
}
</script>
