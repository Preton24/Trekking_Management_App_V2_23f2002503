import { createApp } from 'vue'

// Bootstrap 5 CSS and JS (JS is needed for navbar toggles, modals, dropdowns)
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'

import App from './App.vue'
import router from './router.js'

createApp(App).use(router).mount('#app')
