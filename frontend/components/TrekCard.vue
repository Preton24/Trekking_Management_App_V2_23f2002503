<template>
  <!-- One trek as a card. Used on the trekker dashboard and on the browse page. -->
  <div class="card h-100 shadow-sm">
    <div class="card-body d-flex flex-column">
      <div class="d-flex justify-content-between align-items-start mb-1">
        <h2 class="h5 mb-0">{{ trek.name }}</h2>
        <span class="badge" :class="difficultyBadge(trek.difficulty)">{{ trek.difficulty }}</span>
      </div>
      <div class="text-muted mb-2">{{ trek.location }}</div>

      <ul class="list-unstyled small mb-3">
        <li>{{ trek.duration_days }} days &middot; starts {{ trek.start_date }}</li>
        <li>&#8377;{{ trek.price }}</li>
        <li>
          <span v-if="trek.available_slots > 0">Slots left: {{ trek.available_slots }}</span>
          <span v-else class="text-danger fw-semibold">Full</span>
        </li>
      </ul>

      <!-- mt-auto pushes the button to the bottom so cards of different heights line up -->
      <router-link class="btn btn-outline-success mt-auto" :to="'/trekker/treks/' + trek.id">
        View details
      </router-link>
    </div>
  </div>
</template>

<script>
import { difficultyBadge } from '@/ui.js'

export default {
  name: 'TrekCard',
  props: { trek: { type: Object, required: true } },
  methods: { difficultyBadge: difficultyBadge },
}
</script>
