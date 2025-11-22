<template>
  <div>
    <b-modal id="communityApplicationModal" ref="communityApplicationModal" :title="$t('community.modal.application')" @shown="resetApplicationText" no-close-on-backdrop>
      <div class="container-fluid">
        <b-form @submit.stop.prevent="submitApplication">
          <div class="row">
            <div class="col">
              <b-form-fieldset :label="$t('community.application.text')" :state="applicationTextState" :feedback="applicationTextFeedback" :description="$t('community.application.text.description')">
                <b-form-textarea v-model="applicationText" :rows="6" :max-rows="10"></b-form-textarea>
              </b-form-fieldset>
            </div>
          </div>
        </b-form>
      </div>
      <div slot="modal-footer">
        <div class="btn-group" role="group" aria-label="Community application actions">
          <b-btn variant="primary" @click="submitApplication" :disabled="!isApplicationTextValid">
            <i class="fa fa-paper-plane" aria-hidden="true"></i> {{ $t('button.submit') }}
          </b-btn>
          <b-btn @click="hideApplicationModal">
            <i class="fa fa-close" aria-hidden="true"></i> {{ $t('button.cancel') }}
          </b-btn>
        </div>
      </div>
    </b-modal>
  </div>
</template>

<script>
import * as _ from 'lodash'

export default {
  data() {
    return {
      applicationText: ''
    }
  },
  computed: {
    applicationTextFeedback() {
      if (this.isTextEmpty()) {
        return this.$t('community.application.text.feedback.required')
      }

      return ''
    },
    applicationTextState() {
      if (this.isTextEmpty()) {
        return 'danger'
      }

      return 'success'
    },
    isApplicationTextValid() {
      return !this.isTextEmpty()
    }
  },
  methods: {
    hideApplicationModal() {
      this.$refs.communityApplicationModal.hide()
    },
    isTextEmpty() {
      return _.isEmpty(this.applicationText) || _.isEmpty(this.applicationText.trim())
    },
    resetApplicationText() {
      this.applicationText = ''
    },
    submitApplication() {
      if (!this.isApplicationTextValid) {
        return
      }

      this.hideApplicationModal()

      this.$store.dispatch('applyToCommunity', {
        communitySlug: this.$route.params.communitySlug,
        applicationText: this.applicationText
      })
    }
  }
}
</script>
