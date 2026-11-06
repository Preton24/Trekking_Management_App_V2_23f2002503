<template>
  <div class="container py-4">
    <h1 class="h3 mb-3">Browse treks</h1>

    <!-- Filters. Pressing Search (or Enter) asks the backend for matching Open treks. -->
    <form class="row g-2 mb-4" @submit.prevent="load">
      <div class="col-12 col-md-4">
        <input v-model.trim="q" type="search" class="form-control" placeholder="Search by name, place or description"
               aria-label="Search treks" />
      </div>
      <div class="col-6 col-md-2">
        <select v-model="difficulty" class="form-select" aria-label="Difficulty">
          <option value="">Any difficulty</option>
          <option>Easy</option>
          <option>Moderate</option>
          <option>Hard</option>
        </select>
      </div>
      <div class="col-6 col-md-2">
        <input v-model.trim="location" type="text" class="form-control" placeholder="Location" aria-label="Location" />
      </div>
      <div class="col-6 col-md-1">
        <input v-model="minDuration" type="number" min="1" step="1" class="form-control" placeholder="Min days"
               aria-label="Minimum days" />
      </div>
      <div class="col-6 col-md-1">
        <input v-model="maxDuration" type="number" min="1" step="1" class="form-control" placeholder="Max days"
               aria-label="Maximum days" />
      </div>
      <div class="col-12 col-md-2 d-flex gap-2">
        <button class="btn btn-success flex-fill" type="submit">Search</button>
        <button class="btn btn-outline-secondary" type="button" @click="clearFilters">Clear</button>
      </div>
    </form>

    <div v-if="loading" class="text-muted">Loading treks...</div>
    <div v-else-if="treks.length === 0" class="alert alert-secondary">No open treks match your filters.</div>

    <!-- 1 card per row on phones, 2 on tablets, 3 on desktops -->
    <div v-else class="row g-3">
      <div v-for="trek in treks" :key="trek.id" class="col-12 col-md-6 col-lg-4">
        <TrekCard :trek="trek" />
      </div>
    </div>
  </div>
</template>

<script>
import TrekCard from '@components/TrekCard.vue'
import { apiFetch } from '@/api.js'
import { showToast } from '@/toast.js'

export default {
  name: 'TrekBrowse',
  components: { TrekCard },
  data() {
    return { treks: [], q: '', difficulty: '', location: '', minDuration: '', maxDuration: '', loading: true }
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      // Only filters that have a value are added to the URL
      const params = new URLSearchParams()
      if (this.q) params.append('q', this.q)
      if (this.difficulty) params.append('difficulty', this.difficulty)
      if (this.location) params.append('location', this.location)
      if (this.minDuration) params.append('min_duration', this.minDuration)
      if (this.maxDuration) params.append('max_duration', this.maxDuration)

      try {
        this.treks = await apiFetch('/api/treks?' + params.toString())
      } catch (err) {
        showToast(err.message, 'danger') // e.g. minimum days greater than maximum days
      } finally {
        this.loading = false
      }
    },
    clearFilters() {
      this.q = ''
      this.difficulty = ''
      this.location = ''
      this.minDuration = ''
      this.maxDuration = ''
      this.load()
    },
  },
}
</script>
