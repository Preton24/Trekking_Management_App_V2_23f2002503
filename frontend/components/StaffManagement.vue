<template>
  <div class="container py-4">
    <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
      <h1 class="h3 mb-0">Manage trek staff</h1>
      <button class="btn btn-success" type="button" @click="openCreate">+ Create staff</button>
    </div>

    <div v-if="loading" class="text-muted">Loading staff...</div>
    <div v-else-if="staff.length === 0" class="alert alert-secondary">No staff accounts yet.</div>

    <div v-else class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr>
            <th>Name</th><th>Email</th><th>Contact</th><th>Experience</th>
            <th>Profile</th><th>Account</th><th class="text-end">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="person in staff" :key="person.id">
            <td class="fw-semibold">{{ person.name }}</td>
            <td>{{ person.email }}</td>
            <td>{{ person.staff_profile ? person.staff_profile.contact : '-' }}</td>
            <td>{{ person.staff_profile ? person.staff_profile.experience : 0 }} yrs</td>
            <td>{{ person.staff_profile ? person.staff_profile.status : '-' }}</td>
            <td>
              <span v-if="person.is_blacklisted" class="badge bg-danger">Blacklisted</span>
              <span v-else-if="!person.is_active" class="badge bg-secondary">Inactive</span>
              <span v-else class="badge bg-success">Active</span>
            </td>
            <td class="text-end text-nowrap">
              <button class="btn btn-sm btn-outline-primary me-1" type="button" @click="openEdit(person)">Edit</button>
              <button v-if="!person.is_blacklisted" class="btn btn-sm btn-outline-danger me-1" type="button"
                      @click="askBlacklist(person)">Blacklist</button>
              <button v-else class="btn btn-sm btn-outline-success me-1" type="button"
                      @click="activate(person)">Activate</button>
              <button class="btn btn-sm btn-danger" type="button" @click="askDelete(person)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create / edit modal -->
    <div ref="modalEl" class="modal fade" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <form ref="form" :class="{ 'was-validated': submitted }" novalidate @submit.prevent="save">
            <div class="modal-header">
              <h5 class="modal-title">{{ isEdit ? 'Edit staff' : 'Create staff' }}</h5>
              <button type="button" class="btn-close" aria-label="Close" @click="modal.hide()"></button>
            </div>
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label" for="s-name">Full name</label>
                <input id="s-name" v-model.trim="form.name" class="form-control" maxlength="100" required />
                <div class="invalid-feedback">Name is required.</div>
              </div>
              <div class="mb-3">
                <label class="form-label" for="s-email">Email</label>
                <input id="s-email" v-model.trim="form.email" type="email" class="form-control" required />
                <div class="invalid-feedback">Enter a valid email address.</div>
              </div>
              <div class="mb-3">
                <label class="form-label" for="s-pass">
                  Password <span v-if="isEdit" class="text-muted">(leave empty to keep the current one)</span>
                </label>
                <!-- Required only when creating. On edit, minlength still applies if something is typed. -->
                <input id="s-pass" v-model="form.password" type="password" class="form-control"
                       minlength="6" autocomplete="new-password" :required="!isEdit" />
                <div class="invalid-feedback">Password must be at least 6 characters.</div>
              </div>
              <div class="mb-3">
                <label class="form-label" for="s-phone">Phone <span class="text-muted">(optional)</span></label>
                <input id="s-phone" v-model.trim="form.phone" type="tel" class="form-control"
                       pattern="[0-9]{10}" maxlength="10" inputmode="numeric" />
                <div class="invalid-feedback">Enter a 10 digit phone number, or leave it empty.</div>
              </div>
              <div class="mb-3">
                <label class="form-label" for="s-contact">Work contact / base office</label>
                <input id="s-contact" v-model.trim="form.contact" class="form-control" maxlength="100" />
              </div>
              <div class="row">
                <div class="col-6 mb-3">
                  <label class="form-label" for="s-exp">Experience (years)</label>
                  <input id="s-exp" v-model="form.experience" type="number" min="0" step="1"
                         class="form-control" required />
                  <div class="invalid-feedback">Enter 0 or more.</div>
                </div>
                <div v-if="isEdit" class="col-6 mb-3">
                  <label class="form-label" for="s-status">Profile status</label>
                  <select id="s-status" v-model="form.status" class="form-select">
                    <option>Active</option>
                    <option>Inactive</option>
                  </select>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-outline-secondary" @click="modal.hide()">Cancel</button>
              <button type="submit" class="btn btn-success" :disabled="saving">
                {{ saving ? 'Saving...' : 'Save' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <ConfirmModal ref="confirm" />
  </div>
</template>

<script>
import { Modal } from 'bootstrap'
import ConfirmModal from '@components/ConfirmModal.vue'
import { apiFetch } from '@/api.js'
import { showToast } from '@/toast.js'

function emptyForm() {
  return { id: null, name: '', email: '', password: '', phone: '', contact: '', experience: 0, status: 'Active' }
}

export default {
  name: 'StaffManagement',
  components: { ConfirmModal },
  data() {
    return { staff: [], loading: true, form: emptyForm(), isEdit: false, submitted: false, saving: false }
  },
  mounted() {
    this.modal = new Modal(this.$refs.modalEl)
    this.load()
  },
  beforeUnmount() {
    this.modal.dispose()
  },
  methods: {
    async load() {
      try {
        this.staff = await apiFetch('/api/admin/staff')
      } catch (err) {
        showToast(err.message, 'danger')
      } finally {
        this.loading = false
      }
    },

    openCreate() {
      this.isEdit = false
      this.form = emptyForm()
      this.submitted = false
      this.modal.show()
    },
    openEdit(person) {
      this.isEdit = true
      const profile = person.staff_profile || {}
      this.form = {
        id: person.id, name: person.name, email: person.email, password: '',
        phone: person.phone || '', contact: profile.contact || '',
        experience: profile.experience || 0, status: profile.status || 'Active',
      }
      this.submitted = false
      this.modal.show()
    },

    async save() {
      this.submitted = true
      if (!this.$refs.form.checkValidity()) {
        return
      }

      const body = {
        name: this.form.name,
        email: this.form.email,
        phone: this.form.phone,
        contact: this.form.contact,
        experience: Number(this.form.experience),
      }
      // On create the password is required; on edit it is only sent if the admin typed one
      if (this.form.password) {
        body.password = this.form.password
      }
      if (this.isEdit) {
        body.status = this.form.status
      }

      this.saving = true
      try {
        const url = this.isEdit ? '/api/admin/staff/' + this.form.id : '/api/admin/staff'
        const data = await apiFetch(url, { method: this.isEdit ? 'PUT' : 'POST', body: body })
        this.modal.hide()
        showToast(data.message)
        this.load()
      } catch (err) {
        showToast(err.message, 'danger') // e.g. "An account with this email already exists."
      } finally {
        this.saving = false
      }
    },

    askBlacklist(person) {
      this.$refs.confirm.ask({
        title: 'Blacklist staff',
        message: person.name + ' will be blocked from logging in straight away. Continue?',
        confirmText: 'Blacklist',
        onConfirm: () => this.changeAccess(person, 'blacklist'),
      })
    },
    activate(person) {
      this.changeAccess(person, 'activate')
    },
    async changeAccess(person, action) {
      try {
        const data = await apiFetch('/api/admin/users/' + person.id + '/' + action, { method: 'PUT' })
        showToast(data.message)
        this.load()
      } catch (err) {
        showToast(err.message, 'danger')
      }
    },

    askDelete(person) {
      this.$refs.confirm.ask({
        title: 'Delete staff',
        message: 'Delete the account of ' + person.name + '? This cannot be undone.',
        confirmText: 'Delete',
        onConfirm: () => this.deleteStaff(person),
      })
    },
    async deleteStaff(person) {
      try {
        const data = await apiFetch('/api/admin/staff/' + person.id, { method: 'DELETE' })
        showToast(data.message)
        this.load()
      } catch (err) {
        // Refused while the person still leads a trek
        showToast(err.message, 'danger')
      }
    },
  },
}
</script>
