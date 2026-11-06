// Tiny shared store for toast messages. Any page can call showToast(...);
// ToastContainer.vue (mounted once in App.vue) draws whatever is in this list.
import { reactive } from 'vue'

export const toasts = reactive([])
let nextId = 1

// type is 'success' (green) or 'danger' (red)
export function showToast(message, type = 'success') {
  const id = nextId++
  toasts.push({ id: id, message: message, type: type })
  // Remove it automatically after 4 seconds
  setTimeout(() => removeToast(id), 4000)
}

export function removeToast(id) {
  const index = toasts.findIndex((t) => t.id === id)
  if (index !== -1) {
    toasts.splice(index, 1)
  }
}
