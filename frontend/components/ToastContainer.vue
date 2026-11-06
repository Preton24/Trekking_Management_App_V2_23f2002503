<template>
  <!-- Fixed to the top-right corner; z-index is above Bootstrap modals so toasts show over them -->
  <div class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 2000">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="toast show align-items-center border-0"
      :class="toast.type === 'danger' ? 'text-bg-danger' : 'text-bg-success'"
      role="alert"
    >
      <div class="d-flex">
        <div class="toast-body">{{ toast.message }}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" aria-label="Close"
                @click="remove(toast.id)"></button>
      </div>
    </div>
  </div>
</template>

<script>
import { toasts, removeToast } from '@/toast.js'

export default {
  name: 'ToastContainer',
  data() {
    return { toasts: toasts }
  },
  methods: {
    remove(id) {
      removeToast(id)
    },
  },
}
</script>
