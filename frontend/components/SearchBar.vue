<template>
  <!-- Global admin search. It only collects the text; AdminSearch.vue shows the results. -->
  <form class="d-flex" role="search" @submit.prevent="search">
    <input v-model.trim="text" class="form-control form-control-sm me-2" type="search"
           placeholder="Search treks, users, staff" aria-label="Search" required />
    <button class="btn btn-light btn-sm" type="submit">Search</button>
  </form>
</template>

<script>
export default {
  name: 'SearchBar',
  emits: ['searched'],
  data() {
    return { text: '' }
  },
  methods: {
    search() {
      if (!this.text) {
        return
      }
      this.$router.push({ path: '/admin/search', query: { q: this.text } })
      this.$emit('searched') // lets the Navbar close its mobile menu
    },
  },
}
</script>
