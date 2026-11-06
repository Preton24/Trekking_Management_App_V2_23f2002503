<template>
  <div class="container py-4">
    <h1 class="h3">My dashboard</h1>
    <p class="text-muted">Welcome, {{ auth.name }}. These are the treks assigned to you.</p>

    <div v-if="loading" class="text-muted">Loading your treks...</div>

    <div v-else>
      <!-- Summary numbers -->
      <div class="row g-3 mb-4">
        <div v-for="card in cards" :key="card.label" class="col-12 col-sm-4">
          <div class="card shadow-sm h-100">
            <div class="card-body">
              <div class="text-muted small">{{ card.label }}</div>
              <div class="display-6">{{ card.value }}</div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="treks.length === 0" class="alert alert-secondary">
        No treks are assigned to you yet. The admin will assign them.
      </div>

      <div class="row g-3">
        <div v-for="trek in treks" :key="trek.id" class="col-12 col-md-6 col-xl-4">
          <div class="card h-100 shadow-sm">
            <div class="card-body d-flex flex-column">
              <div class="d-flex justify-content-between align-items-start mb-1">
                <h2 class="h5 mb-0">{{ trek.name }}</h2>
                <span class="badge" :class="statusBadge(trek.status)">{{ trek.status }}</span>
              </div>
              <div class="text-muted small mb-2">{{ trek.location }} &middot; {{ trek.difficulty }}</div>
              <div class="small mb-2">{{ trek.start_date }} to {{ trek.end_date }}</div>

              <!-- Registered vs capacity -->
              <div class="small mb-1">
                <strong>{{ trek.registered_count }}</strong> registered of {{ trek.total_slots }} slots
                ({{ trek.available_slots }} left)
              </div>
              <div class="progress mb-3" role="progressbar" style="height: 8px"
                   :aria-valuenow="trek.registered_count" aria-valuemin="0" :aria-valuemax="trek.total_slots">
                <div class="progress-bar bg-success" :style="{ width: percentFull(trek) + '%' }"></div>
              </div>

              <!-- Buttons only appear when that action is allowed for the trek's current status.
                   The backend enforces the same rules. -->
              <div class="d-flex flex-wrap gap-2 mt-auto">
                <button class="btn btn-sm btn-outline-secondary" type="button" @click="openParticipants(trek)">
                  Participants
                </button>
                <button v-if="canEdit(trek)" class="btn btn-sm btn-outline-primary" type="button"
                        @click="openEdit(trek)">Update slots/status</button>
                <button v-if="canStart(trek)" class="btn btn-sm btn-success" type="button"
                        @click="askStart(trek)">Start trek</button>
                <button v-if="trek.status === 'Ongoing'" class="btn btn-sm btn-primary" type="button"
                        @click="askComplete(trek)">Mark completed</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Update slots / status modal -->
    <div ref="editEl" class="modal fade" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <form ref="form" :class="{ 'was-validated': submitted }" novalidate @submit.prevent="saveEdit">
            <div class="modal-header">
              <h5 class="modal-title">Update {{ editing ? editing.name : '' }}</h5>
              <button type="button" class="btn-close" aria-label="Close" @click="editModal.hide()"></button>
            </div>
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label" for="e-slots">Total slots</label>
                <!-- min is the number already booked, so the browser itself blocks going below it -->
                <input id="e-slots" v-model="form.total_slots" type="number" step="1"
                       :min="editing ? Math.max(1, editing.registered_count) : 1" class="form-control" required />
                <div class="invalid-feedback">
                  Enter a whole number, at least {{ editing ? Math.max(1, editing.registered_count) : 1 }}
                  (seats already booked).
                </div>
              </div>
              <div class="mb-3">
                <label class="form-label" for="e-status">Booking status</label>
                <select id="e-status" v-model="form.status" class="form-select">
                  <!-- "" keeps the status as it is (needed for an Approved trek) -->
                  <option v-if="editing && editing.status !== 'Open' && editing.status !== 'Closed'" value="">
                    Keep {{ editing.status }}
                  </option>
                  <option value="Open">Open (trekkers can book)</option>
                  <option value="Closed">Closed (no new bookings)</option>
                </select>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-outline-secondary" @click="editModal.hide()">Cancel</button>
              <button type="submit" class="btn btn-success" :disabled="saving">
                {{ saving ? 'Saving...' : 'Save' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Participants modal -->
    <div ref="peopleEl" class="modal fade" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Participants: {{ peopleTrek }} ({{ participants.length }})</h5>
            <button type="button" class="btn-close" aria-label="Close" @click="peopleModal.hide()"></button>
          </div>
          <div class="modal-body">
            <p v-if="peopleLoading" class="text-muted mb-0">Loading...</p>
            <p v-else-if="participants.length === 0" class="text-muted mb-0">Nobody has booked this trek yet.</p>
            <div v-else class="table-responsive">
              <table class="table table-sm align-middle mb-0">
                <thead class="table-light">
                  <tr><th>#</th><th>Name</th><th>Email</th><th>Phone</th><th>Booked on</th><th>Status</th></tr>
                </thead>
                <tbody>
                  <tr v-for="(person, index) in participants" :key="person.booking_id">
                    <td>{{ index + 1 }}</td>
                    <td>{{ person.name }}</td>
                    <td>{{ person.email }}</td>
                    <td>{{ person.phone || '-' }}</td>
                    <td>{{ shortDate(person.booking_date) }}</td>
                    <td><span class="badge" :class="bookingBadge(person.status)">{{ person.status }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
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
import { auth } from '@/auth.js'
import { showToast } from '@/toast.js'
import { bookingStatusBadge, shortDate, trekStatusBadge } from '@/ui.js'

export default {
  name: 'StaffDashboard',
  components: { ConfirmModal },
  data() {
    return {
      auth: auth,
      treks: [],
      loading: true,
      // update modal
      editing: null,
      form: { total_slots: 1, status: 'Open' },
      submitted: false,
      saving: false,
      // participants modal
      participants: [],
      peopleTrek: '',
      peopleLoading: false,
    }
  },
  computed: {
    cards() {
      const participantTotal = this.treks.reduce((sum, t) => sum + t.registered_count, 0)
      const ongoing = this.treks.filter((t) => t.status === 'Ongoing').length
      return [
        { label: 'Assigned treks', value: this.treks.length },
        { label: 'Total participants', value: participantTotal },
        { label: 'Ongoing treks', value: ongoing },
      ]
    },
  },
  mounted() {
    this.editModal = new Modal(this.$refs.editEl)
    this.peopleModal = new Modal(this.$refs.peopleEl)
    this.load()
  },
  beforeUnmount() {
    this.editModal.dispose()
    this.peopleModal.dispose()
  },
  methods: {
    statusBadge: trekStatusBadge,
    bookingBadge: bookingStatusBadge,
    shortDate: shortDate,

    async load() {
      try {
        this.treks = await apiFetch('/api/staff/treks')
      } catch (err) {
        showToast(err.message, 'danger')
      } finally {
        this.loading = false
      }
    },

    percentFull(trek) {
      return Math.min(100, Math.round((trek.registered_count / trek.total_slots) * 100))
    },

    // Which buttons make sense for which status (mirrors the backend rules)
    canEdit(trek) {
      return ['Approved', 'Open', 'Closed'].includes(trek.status)
    },
    canStart(trek) {
      return trek.status === 'Open' || trek.status === 'Closed'
    },

    // ---- update slots / status ----
    openEdit(trek) {
      this.editing = trek
      this.form = {
        total_slots: trek.total_slots,
        status: trek.status === 'Open' || trek.status === 'Closed' ? trek.status : '',
      }
      this.submitted = false
      this.editModal.show()
    },
    async saveEdit() {
      this.submitted = true
      if (!this.$refs.form.checkValidity()) {
        return
      }
      const body = { total_slots: Number(this.form.total_slots) }
      if (this.form.status) {
        body.status = this.form.status
      }
      this.saving = true
      try {
        const data = await apiFetch('/api/staff/treks/' + this.editing.id, { method: 'PUT', body: body })
        this.editModal.hide()
        showToast(data.message)
        this.load()
      } catch (err) {
        showToast(err.message, 'danger')
      } finally {
        this.saving = false
      }
    },

    // ---- participants ----
    async openParticipants(trek) {
      this.peopleTrek = trek.name
      this.participants = []
      this.peopleLoading = true
      this.peopleModal.show()
      try {
        const data = await apiFetch('/api/staff/treks/' + trek.id + '/participants')
        this.participants = data.participants
      } catch (err) {
        showToast(err.message, 'danger')
      } finally {
        this.peopleLoading = false
      }
    },

    // ---- start / complete ----
    askStart(trek) {
      this.$refs.confirm.ask({
        title: 'Start trek',
        message: 'Start "' + trek.name + '"? Trekkers will no longer be able to book or cancel.',
        confirmText: 'Start trek',
        confirmClass: 'btn-success',
        onConfirm: () => this.changeTrek(trek, 'start'),
      })
    },
    askComplete(trek) {
      this.$refs.confirm.ask({
        title: 'Complete trek',
        message: 'Mark "' + trek.name + '" as completed? All its active bookings will be marked Completed.',
        confirmText: 'Mark completed',
        confirmClass: 'btn-primary',
        onConfirm: () => this.changeTrek(trek, 'complete'),
      })
    },
    async changeTrek(trek, action) {
      try {
        const data = await apiFetch('/api/staff/treks/' + trek.id + '/' + action, { method: 'PUT' })
        showToast(data.message)
      } catch (err) {
        showToast(err.message, 'danger')
      }
      this.load()
    },
  },
}
</script>
