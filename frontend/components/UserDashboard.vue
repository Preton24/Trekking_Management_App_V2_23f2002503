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
        <div class="d-flex align-items-center gap-3">
          <!-- Disabled while an export is running, so it cannot be started twice -->
          <button class="btn btn-sm btn-outline-success" type="button"
                  :disabled="exportState === 'working'" @click="startExport">
            Export CSV
          </button>
          <router-link to="/trekker/bookings">View all</router-link>
        </div>
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

    <!-- Export status toast (bottom-right). Unlike the normal toasts it stays open
         until closed, because it has to show progress and then the download link. -->
    <div v-if="exportState" class="toast-container position-fixed bottom-0 end-0 p-3" style="z-index: 2000">
      <div class="toast show" role="status">
        <div class="toast-header">
          <span v-if="exportState === 'working'" class="spinner-border spinner-border-sm text-success me-2"></span>
          <strong class="me-auto">Booking export</strong>
          <button type="button" class="btn-close" aria-label="Close" @click="closeExportToast"></button>
        </div>
        <div class="toast-body">
          <div :class="exportState === 'failed' ? 'text-danger' : ''">{{ exportMessage }}</div>
          <a v-if="exportState === 'done'" class="btn btn-sm btn-success mt-2" :href="exportUrl"
             target="_blank" download>Download CSV</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TrekCard from '@components/TrekCard.vue'
import { apiFetch } from '@/api.js'
import { auth } from '@/auth.js'
import { API_BASE_URL } from '@/config.js'
import { showToast } from '@/toast.js'
import { bookingStatusBadge } from '@/ui.js'

// The export runs in the background on the server, so the page asks for its
// status every 2 seconds, and gives up after 30 checks (1 minute).
const EXPORT_POLL_MS = 2000
const EXPORT_MAX_CHECKS = 30

export default {
  name: 'UserDashboard',
  components: { TrekCard },
  data() {
    return {
      auth: auth,
      treks: [],
      bookings: [],
      loading: true,
      // CSV export: exportState is '' (toast hidden), 'working', 'done' or 'failed'
      exportState: '',
      exportMessage: '',
      exportUrl: '',
      exportTaskId: null,
      exportChecks: 0,
      exportTimer: null,
    }
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
  beforeUnmount() {
    // Stop polling when the user leaves this page
    clearTimeout(this.exportTimer)
  },
  methods: {
    statusBadge: bookingStatusBadge,

    // Step 1: ask the backend to start the export. It replies at once with a task id.
    async startExport() {
      clearTimeout(this.exportTimer)
      this.exportState = 'working'
      this.exportMessage = 'Preparing your CSV file...'
      this.exportUrl = ''
      this.exportChecks = 0
      try {
        const data = await apiFetch('/api/bookings/export', { method: 'POST' })
        this.exportTaskId = data.task_id
        this.exportTimer = setTimeout(this.checkExport, EXPORT_POLL_MS)
      } catch (err) {
        this.exportState = 'failed'
        this.exportMessage = err.message
      }
    },

    // Step 2: ask how the task is doing. Each check schedules the next one itself
    // (instead of setInterval), so two checks can never run at the same time.
    async checkExport() {
      this.exportChecks += 1
      try {
        const data = await apiFetch('/api/tasks/' + this.exportTaskId)
        if (data.state === 'SUCCESS') {
          this.exportState = 'done'
          this.exportMessage = 'Your export is ready (' + data.rows + ' bookings).'
          // The CSV is a static file on the Flask server, so the link needs the backend address
          this.exportUrl = API_BASE_URL + data.download_url
          return
        }
        if (data.state === 'FAILURE') {
          this.exportState = 'failed'
          this.exportMessage = data.error
          return
        }
      } catch (err) {
        this.exportState = 'failed'
        this.exportMessage = err.message
        return
      }

      // Still PENDING or STARTED: try again shortly, unless we have waited too long
      if (this.exportChecks >= EXPORT_MAX_CHECKS) {
        this.exportState = 'failed'
        this.exportMessage = 'The export is taking too long. Please check that the Celery worker is running.'
        return
      }
      this.exportMessage = 'Still working on your CSV file...'
      this.exportTimer = setTimeout(this.checkExport, EXPORT_POLL_MS)
    },

    closeExportToast() {
      clearTimeout(this.exportTimer)
      this.exportState = ''
    },
  },
}
</script>
