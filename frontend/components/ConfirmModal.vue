<template>
  <!-- One reusable "Are you sure?" Bootstrap modal. A page opens it with this.$refs.confirm.ask({...}) -->
  <div ref="el" class="modal fade" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ title }}</h5>
          <button type="button" class="btn-close" aria-label="Close" @click="hide"></button>
        </div>
        <div class="modal-body">{{ message }}</div>
        <div class="modal-footer">
          <button type="button" class="btn btn-outline-secondary" @click="hide">Cancel</button>
          <button type="button" class="btn" :class="confirmClass" @click="confirm">{{ confirmText }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Modal } from 'bootstrap'

export default {
  name: 'ConfirmModal',
  data() {
    return { title: '', message: '', confirmText: 'Confirm', confirmClass: 'btn-danger', onConfirm: null }
  },
  mounted() {
    // Bootstrap's own JS controls showing/hiding the modal
    this.modal = new Modal(this.$refs.el)
  },
  beforeUnmount() {
    this.modal.dispose()
  },
  methods: {
    // options: { title, message, confirmText, confirmClass (Bootstrap button class), onConfirm }
    ask(options) {
      this.title = options.title || 'Are you sure?'
      this.message = options.message
      this.confirmText = options.confirmText || 'Confirm'
      this.confirmClass = options.confirmClass || 'btn-danger'
      this.onConfirm = options.onConfirm
      this.modal.show()
    },
    hide() {
      this.modal.hide()
    },
    confirm() {
      this.modal.hide()
      if (this.onConfirm) {
        this.onConfirm()
      }
    },
  },
}
</script>
