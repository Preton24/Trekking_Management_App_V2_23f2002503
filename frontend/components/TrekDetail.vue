<template>
  <div class="container py-4">
    <router-link to="/trekker/browse" class="small">&larr; Back to treks</router-link>

    <div v-if="loading" class="text-muted mt-3">Loading trek...</div>
    <div v-else-if="!trek" class="alert alert-secondary mt-3">This trek could not be found.</div>

    <div v-else class="row mt-2">
      <div class="col-12 col-lg-8 mb-3">
        <div class="card shadow-sm">
          <div class="card-body">
            <div class="d-flex flex-wrap justify-content-between align-items-start gap-2">
              <h1 class="h3 mb-0">{{ trek.name }}</h1>
              <span class="badge" :class="difficultyBadge(trek.difficulty)">{{ trek.difficulty }}</span>
            </div>
            <div class="text-muted mb-3">{{ trek.location }}</div>
            <p>{{ trek.description || 'No description added yet.' }}</p>

            <!-- Facts in a two-column list that stacks nicely on mobile -->
            <dl class="row mb-0">
              <dt class="col-5 col-sm-3">Dates</dt>
              <dd class="col-7 col-sm-9">{{ trek.start_date }} to {{ trek.end_date }} ({{ trek.duration_days }} days)</dd>
              <dt class="col-5 col-sm-3">Price</dt>
              <dd class="col-7 col-sm-9">&#8377;{{ trek.price }}</dd>
              <dt class="col-5 col-sm-3">Led by</dt>
              <dd class="col-7 col-sm-9">{{ trek.assigned_staff_name || 'To be announced' }}</dd>
              <dt class="col-5 col-sm-3">Slots left</dt>
              <dd class="col-7 col-sm-9">{{ trek.available_slots }} of {{ trek.total_slots }}</dd>
              <dt class="col-5 col-sm-3">Status</dt>
              <dd class="col-7 col-sm-9"><span class="badge" :class="statusBadge(trek.status)">{{ trek.status }}</span></dd>
            </dl>
          </div>
        </div>
      </div>

      <div class="col-12 col-lg-4">
        <div class="card shadow-sm">
          <div class="card-body">
            <!-- The button is disabled in the cases the backend would refuse anyway,
                 and the text says why. The backend still checks everything on its own. -->
            <button class="btn btn-success w-100" type="button" :disabled="!canBook || booking" @click="book">
              {{ booking ? 'Booking...' : buttonText }}
            </button>
            <router-link v-if="trek.already_booked" to="/trekker/bookings" class="btn btn-link w-100 mt-2">
              View my bookings
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { apiFetch } from '@/api.js'
import { showToast } from '@/toast.js'
import { difficultyBadge, trekStatusBadge } from '@/ui.js'

export default {
  name: 'TrekDetail',
  data() {
    return { trek: null, loading: true, booking: false }
  },
  computed: {
    canBook() {
      return this.trek && this.trek.status === 'Open' && this.trek.available_slots > 0 && !this.trek.already_booked
    },
    buttonText() {
      if (this.trek.already_booked) return 'Already booked'
      if (this.trek.status !== 'Open') return 'Not open for booking'
      if (this.trek.available_slots <= 0) return 'Trek is full'
      return 'Book now'
    },
  },
  mounted() {
    this.load()
  },
  methods: {
    difficultyBadge: difficultyBadge,
    statusBadge: trekStatusBadge,

    async load() {
      try {
        this.trek = await apiFetch('/api/treks/' + this.$route.params.id)
      } catch (err) {
        this.trek = null
        showToast(err.message, 'danger')
      } finally {
        this.loading = false
      }
    },

    async book() {
      this.booking = true
      try {
        const data = await apiFetch('/api/treks/' + this.trek.id + '/book', { method: 'POST' })
        showToast(data.message + ' Your seat is confirmed.')
      } catch (err) {
        // e.g. "Sorry, the last slot was just taken."
        showToast(err.message, 'danger')
      } finally {
        this.booking = false
        // Reload either way so the slot count and the button show the real state
        this.load()
      }
    },
  },
}
</script>
