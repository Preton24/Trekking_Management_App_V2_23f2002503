<template>
  <div class="container py-4">
    <div class="row justify-content-center">
      <div class="col-12 col-md-8 col-lg-6">
        <h1 class="h3 mb-3">My profile</h1>

        <div v-if="loading" class="text-muted">Loading profile...</div>

        <div v-else class="card shadow-sm">
          <div class="card-body p-4">
            <form ref="form" :class="{ 'was-validated': submitted }" novalidate @submit.prevent="save">
              <div class="mb-3">
                <label class="form-label" for="p-name">Full name</label>
                <input id="p-name" v-model.trim="form.name" class="form-control" minlength="2" maxlength="100" required />
                <div class="invalid-feedback">Please enter your name (at least 2 letters).</div>
              </div>

              <div class="mb-3">
                <label class="form-label" for="p-email">Email</label>
                <!-- Read-only: the email is the login id and cannot be changed here -->
                <input id="p-email" :value="email" class="form-control" type="email" readonly />
              </div>

              <div class="mb-3">
                <label class="form-label" for="p-phone">Contact number</label>
                <input id="p-phone" v-model.trim="form.phone" type="tel" class="form-control"
                       pattern="[0-9]{10}" maxlength="10" inputmode="numeric" />
                <div class="invalid-feedback">Enter a 10 digit phone number, or leave it empty.</div>
              </div>

              <p class="small text-muted">Member since {{ joined }}</p>

              <button class="btn btn-success w-100" type="submit" :disabled="saving">
                {{ saving ? 'Saving...' : 'Save changes' }}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { apiFetch } from '@/api.js'
import { updateName } from '@/auth.js'
import { showToast } from '@/toast.js'
import { shortDate } from '@/ui.js'

export default {
  name: 'Profile',
  data() {
    return { form: { name: '', phone: '' }, email: '', joined: '', loading: true, saving: false, submitted: false }
  },
  async mounted() {
    try {
      const user = await apiFetch('/api/profile')
      this.form.name = user.name
      this.form.phone = user.phone || ''
      this.email = user.email
      this.joined = shortDate(user.created_at)
    } catch (err) {
      showToast(err.message, 'danger')
    } finally {
      this.loading = false
    }
  },
  methods: {
    async save() {
      this.submitted = true
      if (!this.$refs.form.checkValidity()) {
        return
      }
      this.saving = true
      try {
        const data = await apiFetch('/api/profile', {
          method: 'PUT',
          body: { name: this.form.name, phone: this.form.phone },
        })
        updateName(data.user.name) // so the navbar greets the new name straight away
        showToast(data.message)
      } catch (err) {
        showToast(err.message, 'danger')
      } finally {
        this.saving = false
      }
    },
  },
}
</script>
