import { createRouter, createWebHistory } from 'vue-router'

// Page components live in frontend/components/ (outside src/), imported via the alias
import HomePage from '@components/HomePage.vue'

const routes = [
  { path: '/', name: 'home', component: HomePage },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
