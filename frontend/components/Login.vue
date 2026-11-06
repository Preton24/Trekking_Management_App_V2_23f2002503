<template>
  <div class="container py-4 py-md-5">
    <div class="row justify-content-center">
      <div class="col-12 col-sm-10 col-md-7 col-lg-5">
        <div class="card shadow-sm">
          <div class="card-body p-4">
            <h1 class="h3 mb-1">Welcome back</h1>
            <p class="text-muted">Log in as admin, trek staff or trekker.</p>

            <!-- Shown after a successful signup (Register sends ?registered=1) -->
            <div v-if="$route.query.registered" class="alert alert-success">
              Registration successful. Please log in.
            </div>
            <!-- Error from the backend, e.g. wrong password -->
            <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

            <!-- novalidate turns off the browser's pop-up bubbles; we show Bootstrap's messages instead.
                 The HTML5 rules (required, type=email, minlength) are still checked in submit(). -->
            <form ref="form" :class="{ 'was-validated': submitted }" novalidate @submit.prevent="submit">
              <div class="mb-3">
                <label for="email" class="form-label">Email</label>
                <input
                  id="email"
                  v-model.trim="email"
                  type="email"
                  class="form-control"
                  placeholder="you@example.com"
                  autocomplete="email"
                  required
                />
                <div class="invalid-feedback">Please enter a valid email address.</div>
              </div>

              <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input
                  id="password"
                  v-model="password"
                  type="password"
                  class="form-control"
                  autocomplete="current-password"
                  required
                />
                <div class="invalid-feedback">Please enter your password.</div>
              </div>

              <button type="submit" class="btn btn-success w-100" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
                {{ loading ? 'Logging in...' : 'Login' }}
              </button>
            </form>

            <p class="text-center mt-3 mb-0">
              New trekker? <router-link to="/register">Create an account</router-link>
            </p>
          </div>
        </div>

        <p class="small text-muted text-center mt-3">
          Only trekkers can register themselves. Trek staff accounts are created by the admin.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { apiFetch } from '@/api.js'
import { saveLogin, dashboardPath } from '@/auth.js'

export default {
  name: 'Login',
  data() {
    return {
      email: '',
      password: '',
      submitted: false, // true after the first click, which turns on Bootstrap's red/green styling
      loading: false,
      error: '',
    }
  },
  methods: {
    async submit() {
      this.submitted = true
      this.error = ''

      // checkValidity() applies the HTML5 rules written on the inputs
      if (!this.$refs.form.checkValidity()) {
        return
      }

      this.loading = true
      try {
        const data = await apiFetch('/api/auth/login', {
          method: 'POST',
          body: { email: this.email, password: this.password },
          auth: false, // no token exists yet
        })
        saveLogin(data)
        // Send each role to its own dashboard
        this.$router.push(dashboardPath(data.role))
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
