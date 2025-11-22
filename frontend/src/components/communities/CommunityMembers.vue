<template>
  <div>
    <community-members-table></community-members-table>
    <div class="text-center">
      <div class="btn-group" role="group" aria-label="Community members actions">
        <b-btn variant="secondary" @click="refreshCommunityMembers">
          <i class="fa fa-refresh" aria-hidden="true"></i> {{ $t('button.refresh') }}
        </b-btn>
        <b-btn variant="primary" v-if="loggedIn" :disabled="isCommunityMember || communityApplicationStatus !== null" v-b-modal.communityApplicationModal>
          <i class="fa fa-user-plus" aria-hidden="true"></i> {{ $t('button.apply') }}
        </b-btn>
      </div>
    </div>
    <community-application-modal v-if="loggedIn"></community-application-modal>
  </div>
</template>

<script>
import CommunityMembersTable from './CommunityMembersTable.vue'
import CommunityApplicationModal from './modals/CommunityApplicationModal.vue'

export default {
  components: {
    CommunityMembersTable,
    CommunityApplicationModal
  },
  computed: {
    communityApplicationStatus() {
      return this.$store.getters.communityApplicationStatus
    },
    isCommunityMember() {
      const user = this.$store.getters.user

      if (_.isNil(user)) {
        return false
      } else if (_.isNil(user.community)) {
        return false
      }

      return user.community.slug === this.$route.params.communitySlug
    },
    loggedIn() {
      return this.$store.getters.loggedIn
    }
  },
  methods: {
    refreshCommunityMembers() {
      this.$store.dispatch('getCommunityDetails', this.$route.params.communitySlug)
    }
  }
}
</script>
