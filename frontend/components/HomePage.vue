<template>
  <div class="container py-5">
    <h1>Trekking Management</h1>
    <p class="text-muted">Backend status: {{ status }}</p>
  </div>
</template>

<script>
import { API_BASE_URL } from '@/config.js'

export default {
  name: 'HomePage',
  data() {
    return { status: 'checking...' }
  },
  // On load, call the Flask health route to confirm frontend and backend are connected
  async mounted() {
    try {
      const response = await fetch(API_BASE_URL + '/api/health')
      const data = await response.json()
      this.status = data.status
    } catch (error) {
      this.status = 'not reachable (is Flask running on port 5001?)'
    }
  },
}
</script>
