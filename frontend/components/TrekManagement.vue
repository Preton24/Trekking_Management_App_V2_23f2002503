<template>
  <div class="container py-4">
    <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
      <h1 class="h3 mb-0">Manage treks</h1>
      <button class="btn btn-success" type="button" @click="openCreate">+ Add new trek</button>
    </div>

    <div v-if="loading" class="text-muted">Loading treks...</div>
    <div v-else-if="treks.length === 0" class="alert alert-secondary">No treks yet. Add the first one.</div>

    <!-- table-responsive lets the wide table scroll sideways on a phone -->
    <div v-else class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr>
            <th>Trek</th><th>Difficulty</th><th>Dates</th><th>Slots left</th>
            <th>Price</th><th>Status</th><th>Assigned staff</th><th class="text-end">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="trek in treks" :key="trek.id">
            <td>
              <div class="fw-semibold">{{ trek.name }}</div>
              <div class="small text-muted">{{ trek.location }}</div>
            </td>
            <td>{{ trek.difficulty }}</td>
            <td class="text-nowrap small">{{ trek.start_date }}<br />to {{ trek.end_date }}</td>
            <td>{{ trek.available_slots }} / {{ trek.total_slots }}</td>
            <td>&#8377;{{ trek.price }}</td>
            <td><span class="badge" :class="statusBadge(trek.status)">{{ trek.status }}</span></td>
            <td style="min-width: 170px">
              <!-- Choosing a staff member calls the assign API straight away -->
              <select class="form-select form-select-sm" :value="trek.assigned_staff_id || ''"
                      :aria-label="'Assign staff to ' + trek.name"
                      @change="assignStaff(trek, $event.target.value)">
                <option value="" disabled>Not assigned</option>
                <option v-for="person in staffOptionsFor(trek)" :key="person.id" :value="person.id">
                  {{ person.name }}
                </option>
              </select>
            </td>
            <td class="text-end text-nowrap">
              <button class="btn btn-sm btn-outline-primary me-1" type="button" @click="openEdit(trek)">Edit</button>
              <button class="btn btn-sm btn-outline-danger" type="button" @click="askDelete(trek)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create / edit modal (the same form is used for both) -->
    <div ref="modalEl" class="modal fade" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <form ref="form" :class="{ 'was-validated': submitted }" novalidate @submit.prevent="save">
            <div class="modal-header">
              <h5 class="modal-title">{{ isEdit ? 'Edit trek' : 'Add new trek' }}</h5>
              <button type="button" class="btn-close" aria-label="Close" @click="modal.hide()"></button>
            </div>
            <div class="modal-body">
              <div class="row g-3">
                <div class="col-12 col-md-6">
                  <label class="form-label" for="t-name">Trek name</label>
                  <input id="t-name" v-model.trim="form.name" class="form-control" maxlength="150" required />
                  <div class="invalid-feedback">Trek name is required.</div>
                </div>
                <div class="col-12 col-md-6">
                  <label class="form-label" for="t-loc">Location</label>
                  <input id="t-loc" v-model.trim="form.location" class="form-control" maxlength="150" required />
                  <div class="invalid-feedback">Location is required.</div>
                </div>
                <div class="col-12">
                  <label class="form-label" for="t-desc">Description</label>
                  <textarea id="t-desc" v-model="form.description" class="form-control" rows="2"></textarea>
                </div>
                <div class="col-6 col-md-3">
                  <label class="form-label" for="t-diff">Difficulty</label>
                  <select id="t-diff" v-model="form.difficulty" class="form-select" required>
                    <option v-for="d in difficulties" :key="d" :value="d">{{ d }}</option>
                  </select>
                </div>
                <div class="col-6 col-md-3">
                  <label class="form-label" for="t-status">Status</label>
                  <select id="t-status" v-model="form.status" class="form-select" required>
                    <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
                  </select>
                </div>
                <div class="col-6 col-md-3">
                  <label class="form-label" for="t-slots">Total slots</label>
                  <input id="t-slots" v-model="form.total_slots" type="number" min="1" step="1"
                         class="form-control" required />
                  <div class="invalid-feedback">Enter a whole number, 1 or more.</div>
                </div>
                <div class="col-6 col-md-3">
                  <label class="form-label" for="t-price">Price (&#8377;)</label>
                  <input id="t-price" v-model="form.price" type="number" min="0" step="1"
                         class="form-control" required />
                  <div class="invalid-feedback">Enter a price, 0 or more.</div>
                </div>
                <div class="col-12 col-md-6">
                  <label class="form-label" for="t-start">Start date</label>
                  <input id="t-start" v-model="form.start_date" type="date" class="form-control" required />
                  <div class="invalid-feedback">Start date is required.</div>
                </div>
                <div class="col-12 col-md-6">
                  <label class="form-label" for="t-end">End date</label>
                  <input id="t-end" ref="endDate" v-model="form.end_date" type="date" class="form-control" required />
                  <div class="invalid-feedback">End date must be after the start date.</div>
                </div>
              </div>
              <p class="small text-muted mt-3 mb-0">
                Duration is worked out from the dates. Assign a staff member from the table after saving.
              </p>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-outline-secondary" @click="modal.hide()">Cancel</button>
              <button type="submit" class="btn btn-success" :disabled="saving">
                {{ saving ? 'Saving...' : 'Save trek' }}
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
import { trekStatusBadge } from '@/ui.js'

// Same lists as the backend (Trek.DIFFICULTIES / Trek.STATUSES). The backend re-checks them anyway.
const DIFFICULTIES = ['Easy', 'Moderate', 'Hard']
const STATUSES = ['Pending', 'Approved', 'Open', 'Closed', 'Ongoing', 'Completed']

function emptyForm() {
  return {
    id: null, name: '', location: '', description: '', difficulty: 'Easy', status: 'Pending',
    total_slots: 10, price: 0, start_date: '', end_date: '',
  }
}

export default {
  name: 'TrekManagement',
  components: { ConfirmModal },
  data() {
    return {
      treks: [],
      staff: [],
      loading: true,
      difficulties: DIFFICULTIES,
      statuses: STATUSES,
      form: emptyForm(),
      isEdit: false,
      submitted: false,
      saving: false,
    }
  },
  mounted() {
    this.modal = new Modal(this.$refs.modalEl)
    this.load()
  },
  beforeUnmount() {
    this.modal.dispose()
  },
  methods: {
    statusBadge: trekStatusBadge,

    async load() {
      try {
        // Both lists are needed: treks for the table, staff for the dropdowns
        const [treks, staff] = await Promise.all([
          apiFetch('/api/admin/treks'),
          apiFetch('/api/admin/staff'),
        ])
        this.treks = treks
        this.staff = staff
      } catch (err) {
        showToast(err.message, 'danger')
      } finally {
        this.loading = false
      }
    },

    // Only active staff can be assigned (the backend refuses others), but the
    // current assignee is always listed so the dropdown can show their name.
    staffOptionsFor(trek) {
      return this.staff.filter((person) => {
        const profileActive = !person.staff_profile || person.staff_profile.status === 'Active'
        const usable = person.is_active && !person.is_blacklisted && profileActive
        return usable || person.id === trek.assigned_staff_id
      })
    },

    async assignStaff(trek, staffId) {
      try {
        const data = await apiFetch('/api/admin/treks/' + trek.id + '/assign', {
          method: 'PUT',
          body: { staff_id: Number(staffId) },
        })
        showToast(data.message)
      } catch (err) {
        showToast(err.message, 'danger')
      }
      // Reload either way: on failure this also puts the dropdown back to the real value
      this.load()
    },

    openCreate() {
      this.isEdit = false
      this.form = emptyForm()
      this.submitted = false
      this.modal.show()
    },
    openEdit(trek) {
      this.isEdit = true
      this.form = {
        id: trek.id, name: trek.name, location: trek.location, description: trek.description || '',
        difficulty: trek.difficulty, status: trek.status, total_slots: trek.total_slots,
        price: trek.price, start_date: trek.start_date, end_date: trek.end_date,
      }
      this.submitted = false
      this.modal.show()
    },

    async save() {
      this.submitted = true

      // "End after start" is not an HTML5 rule, so set the custom message by hand
      const endInput = this.$refs.endDate
      if (this.form.start_date && this.form.end_date && this.form.end_date <= this.form.start_date) {
        endInput.setCustomValidity('End date must be after the start date')
      } else {
        endInput.setCustomValidity('')
      }
      if (!this.$refs.form.checkValidity()) {
        return
      }

      const body = {
        name: this.form.name,
        location: this.form.location,
        description: this.form.description,
        difficulty: this.form.difficulty,
        status: this.form.status,
        total_slots: Number(this.form.total_slots), // inputs give text; the API wants numbers
        price: Number(this.form.price),
        start_date: this.form.start_date,
        end_date: this.form.end_date,
      }

      this.saving = true
      try {
        const url = this.isEdit ? '/api/admin/treks/' + this.form.id : '/api/admin/treks'
        const data = await apiFetch(url, { method: this.isEdit ? 'PUT' : 'POST', body: body })
        this.modal.hide()
        showToast(data.message)
        this.load()
      } catch (err) {
        // e.g. "Total slots cannot be less than the 3 seats already booked."
        showToast(err.message, 'danger')
      } finally {
        this.saving = false
      }
    },

    askDelete(trek) {
      this.$refs.confirm.ask({
        title: 'Delete trek',
        message: 'Delete "' + trek.name + '"? This cannot be undone.',
        confirmText: 'Delete',
        onConfirm: () => this.deleteTrek(trek),
      })
    },
    async deleteTrek(trek) {
      try {
        const data = await apiFetch('/api/admin/treks/' + trek.id, { method: 'DELETE' })
        showToast(data.message)
        this.load()
      } catch (err) {
        // A trek with bookings is refused by the backend; the message says to Close it instead
        showToast(err.message, 'danger')
      }
    },
  },
}
</script>
