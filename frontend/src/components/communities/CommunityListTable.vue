<template>
  <div>
    <table class="table table-striped" v-if="communities">
      <thead>
        <tr>
          <th style="width: 10%">{{ $t('community.tag') }}</th>
          <th style="width: 30%">{{ $t('community.name') }}</th>
          <th style="width: 20%">{{ $t('community.website') }}</th>
          <th style="width: 10%" class="text-center">{{ $t('community.missions.past') }}</th>
          <th style="width: 10%" class="text-center">{{ $t('community.missions.future') }}</th>
          <th style="width: 10%" class="text-center">{{ $t('misc.actions') }}</th>
        </tr>
      </thead>
      <tbody>
        <community-list-row v-for="community in communities" :community="community" :key="community.uid"></community-list-row>
      </tbody>
      <tfoot v-show="communities.length >= 10">
        <tr>
          <th style="width: 10%">{{ $t('community.tag') }}</th>
          <th style="width: 30%">{{ $t('community.name') }}</th>
          <th style="width: 20%">{{ $t('community.website') }}</th>
          <th style="width: 10%" class="text-center">{{ $t('community.missions.past') }}</th>
          <th style="width: 10%" class="text-center">{{ $t('community.missions.future') }}</th>
          <th style="width: 10%" class="text-center">{{ $t('misc.actions') }}</th>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<script>
import CommunityListRow from './CommunityListRow.vue'

export default {
  components: {
    CommunityListRow
  },
  props: {
    communitiesOverride: {
      type: Array,
      default: null
    }
  },
  computed: {
    communities() {
      return this.communitiesOverride || this.$store.getters.communities
    }
  }
}
</script>
