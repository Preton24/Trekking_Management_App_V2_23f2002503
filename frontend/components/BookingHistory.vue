<template>
  <div class="container py-4">
    <h1 class="h3 mb-3">My bookings</h1>

    <div v-if="loading" class="text-muted">Loading bookings...</div>
    <div v-else-if="bookings.length === 0" class="alert alert-secondary">
      You have no bookings yet. <router-link to="/trekker/browse">Browse treks</router-link>
    </div>

    <div v-else class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr>
            <th>Trek</th><th>Dates</th><th>Booked on</th><th>Price</th><th>Status</th><th class="text-end">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="booking in bookings" :key="booking.id">
            <td>
              <router-link :to="'/trekker/treks/' + booking.trek_id" class="fw-semibold text-decoration-none">
                {{ booking.trek_name }}
              </router-link>
              <div class="small text-muted">{{ booking.trek_location }}</div>
            </td>
            <td class="small text-nowrap">{{ booking.start_date }}<br />to {{ booking.end_date }}</td>
            <td>{{ shortDate(booking.booking_date) }}</td>
            <td>&#8377;{{ booking.price }}</td>
            <td><span class="badge" :class="statusBadge(booking.status)">{{ booking.status }}</span></td>
            <td class="text-end">
              <button v-if="canCancel(booking)" class="btn btn-sm btn-outline-danger" type="button"
                      @click="askCancel(booking)">Cancel</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <ConfirmModal ref="confirm" />
  </div>
</template>

<script>
import ConfirmModal from '@components/ConfirmModal.vue'
import { apiFetch } from '@/api.js'
import { showToast } from '@/toast.js'
import { bookingStatusBadge, shortDate } from '@/ui.js'

export default {
  name: 'BookingHistory',
  components: { ConfirmModal },
  data() {
    return { bookings: [], loading: true }
  },
  mounted() {
    this.load()
  },
  methods: {
    statusBadge: bookingStatusBadge,
    shortDate: shortDate,

    async load() {
      try {
        this.bookings = await apiFetch('/api/bookings/me') // newest first
      } catch (err) {
        showToast(err.message, 'danger')
      } finally {
        this.loading = false
      }
    },

    // Show the Cancel button only when cancelling is possible: an active booking on a trek
    // that has not started. This only hides the button; the backend makes the real decision.
    canCancel(booking) {
      const today = new Date().toLocaleDateString('en-CA') // local date as YYYY-MM-DD
      const notStarted = booking.trek_status !== 'Ongoing' && booking.trek_status !== 'Completed'
      return booking.status === 'Booked' && notStarted && booking.start_date > today
    },

    askCancel(booking) {
      this.$refs.confirm.ask({
        title: 'Cancel booking',
        message: 'Cancel your booking for "' + booking.trek_name + '"? Your seat will be given to someone else.',
        confirmText: 'Cancel booking',
        onConfirm: () => this.cancel(booking),
      })
    },
    async cancel(booking) {
      try {
        const data = await apiFetch('/api/bookings/' + booking.id + '/cancel', { method: 'PUT' })
        showToast(data.message + ' The slot has been released.')
      } catch (err) {
        showToast(err.message, 'danger') // e.g. the trek has already started
      }
      this.load()
    },
  },
}
</script>
