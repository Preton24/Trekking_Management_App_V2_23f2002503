<template>
  <!-- Navbar is shown on every page; it changes its links by role -->
  <Navbar />
  <!-- The router shows the page component that matches the current URL -->
  <router-view />
  <!-- Success / error messages from any page appear here -->
  <ToastContainer />
</template>

<script>
import Navbar from '@components/Navbar.vue'
import ToastContainer from '@components/ToastContainer.vue'

export default {
  name: 'App',
  components: { Navbar, ToastContainer },
}
</script>
