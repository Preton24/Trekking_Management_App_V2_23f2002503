<template>
  <div class="container py-4">
    <h1 class="h3 mb-3">Manage trekkers</h1>

    <!-- Quick filter on the list already loaded (name or email) -->
    <input v-model.trim="filterText" type="search" class="form-control mb-3"
           placeholder="Filter by name or email" aria-label="Filter trekkers" />

    <div v-if="loading" class="text-muted">Loading trekkers...</div>
    <div v-else-if="visibleUsers.length === 0" class="alert alert-secondary">No trekkers found.</div>

    <div v-else class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr><th>Name</th><th>Email</th><th>Phone</th><th>Joined</th><th>Status</th><th class="text-end">Action</th></tr>
        </thead>
        <tbody>
          <tr v-for="user in visibleUsers" :key="user.id">
            <td class="fw-semibold">{{ user.name }}</td>
            <td>{{ user.email }}</td>
            <td>{{ user.phone || '-' }}</td>
            <td>{{ shortDate(user.created_at) }}</td>
            <td>
              <span v-if="user.is_blacklisted" class="badge bg-danger">Blacklisted</span>
              <span v-else-if="!user.is_active" class="badge bg-secondary">Inactive</span>
              <span v-else class="badge bg-success">Active</span>
            </td>
            <td class="text-end">
              <button v-if="!user.is_blacklisted" class="btn btn-sm btn-outline-danger" type="button"
                      @click="askBlacklist(user)">Blacklist</button>
              <button v-else class="btn btn-sm btn-outline-success" type="button"
                      @click="changeAccess(user, 'activate')">Activate</button>
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
import { shortDate } from '@/ui.js'

export default {
  name: 'UserManagement',
  components: { ConfirmModal },
  data() {
    return { users: [], loading: true, filterText: '' }
  },
  computed: {
    visibleUsers() {
      const text = this.filterText.toLowerCase()
      if (!text) {
        return this.users
      }
      return this.users.filter(
        (u) => u.name.toLowerCase().includes(text) || u.email.toLowerCase().includes(text)
      )
    },
  },
  mounted() {
    this.load()
  },
  methods: {
    shortDate: shortDate,

    async load() {
      try {
        this.users = await apiFetch('/api/admin/users') // trekkers by default
      } catch (err) {
        showToast(err.message, 'danger')
      } finally {
        this.loading = false
      }
    },
    askBlacklist(user) {
      this.$refs.confirm.ask({
        title: 'Blacklist trekker',
        message: user.name + ' will not be able to log in or book treks. Continue?',
        confirmText: 'Blacklist',
        onConfirm: () => this.changeAccess(user, 'blacklist'),
      })
    },
    async changeAccess(user, action) {
      try {
        const data = await apiFetch('/api/admin/users/' + user.id + '/' + action, { method: 'PUT' })
        showToast(data.message)
        this.load()
      } catch (err) {
        showToast(err.message, 'danger')
      }
    },
  },
}
</script>
