<template>
  <div class="container py-4 py-md-5">
    <div class="row justify-content-center">
      <div class="col-12 col-sm-10 col-md-7 col-lg-5">
        <div class="card shadow-sm">
          <div class="card-body p-4">
            <h1 class="h3 mb-1">Create your account</h1>
            <p class="text-muted">Register as a trekker to book treks.</p>

            <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

            <form ref="form" :class="{ 'was-validated': submitted }" novalidate @submit.prevent="submit">
              <div class="mb-3">
                <label for="name" class="form-label">Full name</label>
                <input id="name" v-model.trim="name" type="text" class="form-control"
                       autocomplete="name" minlength="2" maxlength="100" required />
                <div class="invalid-feedback">Please enter your name (at least 2 letters).</div>
              </div>

              <div class="mb-3">
                <label for="email" class="form-label">Email</label>
                <input id="email" v-model.trim="email" type="email" class="form-control"
                       placeholder="you@example.com" autocomplete="email" required />
                <div class="invalid-feedback">Please enter a valid email address.</div>
              </div>

              <div class="mb-3">
                <label for="phone" class="form-label">Contact number <span class="text-muted">(optional)</span></label>
                <!-- pattern only runs when something is typed, so an empty phone is fine -->
                <input id="phone" v-model.trim="phone" type="tel" class="form-control"
                       pattern="[0-9]{10}" maxlength="10" inputmode="numeric" autocomplete="tel" />
                <div class="invalid-feedback">Enter a 10 digit phone number, or leave it empty.</div>
              </div>

              <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input id="password" v-model="password" type="password" class="form-control"
                       minlength="6" autocomplete="new-password" required />
                <div class="invalid-feedback">Password must be at least 6 characters.</div>
              </div>

              <div class="mb-3">
                <label for="confirm" class="form-label">Confirm password</label>
                <input id="confirm" ref="confirm" v-model="confirmPassword" type="password"
                       class="form-control" autocomplete="new-password" required />
                <div class="invalid-feedback">The two passwords must match.</div>
              </div>

              <button type="submit" class="btn btn-success w-100" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
                {{ loading ? 'Creating account...' : 'Register' }}
              </button>
            </form>

            <p class="text-center mt-3 mb-0">
              Already have an account? <router-link to="/login">Log in</router-link>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { apiFetch } from '@/api.js'

export default {
  name: 'Register',
  data() {
    return {
      name: '',
      email: '',
      phone: '',
      password: '',
      confirmPassword: '',
      submitted: false,
      loading: false,
      error: '',
    }
  },
  methods: {
    async submit() {
      this.submitted = true
      this.error = ''

      // HTML5 has no built-in "must match another field" rule, so we set a custom
      // validity message by hand: an empty string means valid, any text means invalid.
      const confirmInput = this.$refs.confirm
      if (this.confirmPassword !== this.password) {
        confirmInput.setCustomValidity('Passwords do not match')
      } else {
        confirmInput.setCustomValidity('')
      }

      if (!this.$refs.form.checkValidity()) {
        return
      }

      this.loading = true
      try {
        await apiFetch('/api/auth/register', {
          method: 'POST',
          body: {
            name: this.name,
            email: this.email,
            phone: this.phone,
            password: this.password,
          },
          auth: false,
        })
        // Back to login with a "registration successful" message
        this.$router.push({ path: '/login', query: { registered: '1' } })
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
