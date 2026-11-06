<template>
  <div class="container py-4">
    <h1 class="h3">Admin dashboard</h1>
    <p class="text-muted">Welcome, {{ auth.name }}.</p>

    <!-- Four stat cards: 2 per row on phones, 4 per row on large screens -->
    <div class="row g-3 mb-4">
      <div v-for="card in cards" :key="card.label" class="col-6 col-lg-3">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <div class="text-muted small">{{ card.label }}</div>
            <div class="display-6">{{ card.value }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="row g-3">
      <div class="col-12 col-lg-7">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h2 class="h6">Bookings per trek</h2>
            <!-- The chart needs a box with a set height; maintainAspectRatio is off in the chart options -->
            <div style="height: 300px"><canvas ref="barCanvas"></canvas></div>
            <details class="mt-2 small">
              <summary>View as table</summary>
              <table class="table table-sm mb-0">
                <thead><tr><th>Trek</th><th class="text-end">Bookings</th></tr></thead>
                <tbody>
                  <tr v-for="row in stats.bookings_per_trek" :key="row.trek_id">
                    <td>{{ row.trek_name }}</td><td class="text-end">{{ row.bookings }}</td>
                  </tr>
                </tbody>
              </table>
            </details>
          </div>
        </div>
      </div>

      <div class="col-12 col-lg-5">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h2 class="h6">Treks by status</h2>
            <div style="height: 300px"><canvas ref="doughnutCanvas"></canvas></div>
            <details class="mt-2 small">
              <summary>View as table</summary>
              <table class="table table-sm mb-0">
                <thead><tr><th>Status</th><th class="text-end">Treks</th></tr></thead>
                <tbody>
                  <tr v-for="row in stats.treks_by_status" :key="row.status">
                    <td>{{ row.status }}</td><td class="text-end">{{ row.count }}</td>
                  </tr>
                </tbody>
              </table>
            </details>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Chart from 'chart.js/auto' // 'auto' registers every chart type, so we need no extra setup
import { apiFetch } from '@/api.js'
import { auth } from '@/auth.js'
import { showToast } from '@/toast.js'

// One fixed colour per trek status (same status = same colour every time).
// Order matches the backend's Trek.STATUSES list.
const STATUS_COLOURS = {
  Pending: '#2a78d6',
  Approved: '#eb6834',
  Open: '#1baf7a',
  Closed: '#eda100',
  Ongoing: '#e87ba4',
  Completed: '#008300',
}
const BAR_COLOUR = '#2a78d6' // one series, so one colour
const SURFACE = '#ffffff' // card background, used as the gap between doughnut slices

export default {
  name: 'AdminDashboard',
  data() {
    return {
      auth: auth,
      stats: { bookings_per_trek: [], treks_by_status: [] },
      totals: { total_treks: 0, total_users: 0, total_staff: 0, total_bookings: 0 },
    }
  },
  computed: {
    cards() {
      return [
        { label: 'Total treks', value: this.totals.total_treks },
        { label: 'Total trekkers', value: this.totals.total_users },
        { label: 'Total trek staff', value: this.totals.total_staff },
        { label: 'Total bookings', value: this.totals.total_bookings },
      ]
    },
  },
  async mounted() {
    try {
      const data = await apiFetch('/api/admin/stats')
      this.stats = data
      this.totals = data
      // Wait for Vue to draw the table rows, then draw the charts
      await this.$nextTick()
      this.drawBarChart()
      this.drawDoughnutChart()
    } catch (err) {
      showToast(err.message, 'danger')
    }
  },
  beforeUnmount() {
    // Charts hold on to their canvas, so destroy them when leaving the page
    if (this.barChart) this.barChart.destroy()
    if (this.doughnutChart) this.doughnutChart.destroy()
  },
  methods: {
    drawBarChart() {
      const rows = this.stats.bookings_per_trek
      // Stored on `this` but not in data(), so Vue does not wrap the chart in a reactive proxy
      this.barChart = new Chart(this.$refs.barCanvas, {
        type: 'bar',
        data: {
          labels: rows.map((r) => r.trek_name),
          datasets: [{
            label: 'Bookings',
            data: rows.map((r) => r.bookings),
            backgroundColor: BAR_COLOUR,
            borderRadius: 4, // rounded top of each bar
            maxBarThickness: 36, // thin bars
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } }, // single series: the card title says what it is
          scales: {
            x: { grid: { display: false } },
            // Bookings are whole numbers, so no 0.5 ticks
            y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: '#ececec' } },
          },
        },
      })
    },
    drawDoughnutChart() {
      const rows = this.stats.treks_by_status
      this.doughnutChart = new Chart(this.$refs.doughnutCanvas, {
        type: 'doughnut',
        data: {
          // The count is put in the label so the legend can be read without the colours
          labels: rows.map((r) => r.status + ' (' + r.count + ')'),
          datasets: [{
            data: rows.map((r) => r.count),
            backgroundColor: rows.map((r) => STATUS_COLOURS[r.status]),
            borderColor: SURFACE,
            borderWidth: 2, // thin gap between slices
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom' } },
        },
      })
    },
  },
}
</script>
