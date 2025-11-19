<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="m-0">{{ $t('nav.communities') }}</h2>
      <div style="max-width: 300px; flex: 1; margin-left: 2rem;">
        <input 
          type="search" 
          class="form-control" 
          v-model="searchQuery" 
          :placeholder="$t('community.list.search')"
        />
      </div>
    </div>
    
    <community-list-table v-if="filteredCommunities" :communities-override="filteredCommunities"></community-list-table>
    <nav v-show="communityListPageCount > 1">
      <paginate ref="communityListPaginate" :pageCount="communityListPageCount" :initial-page="0" :clickHandler="communityListPaginate" :container-class="'pagination justify-content-center'" :page-class="'page-item'" :page-link-class="'page-link'" :prev-class="'page-item'" :prev-link-class="'page-link'" :next-class="'page-item'" :next-link-class="'page-link'"></paginate>
    </nav>
    <div class="text-center" v-show="canCreateCommunity">
      <router-link tag="button" type="button" class="btn btn-success" :to="{name: 'communityCreator'}">
        <i class="fa fa-plus" aria-hidden="true"></i> {{ $t('button.create.community') }}
      </router-link>
    </div>
  </div>
</template>

<script>
import CommunityListTable from '../components/communities/CommunityListTable.vue'
import utils from '../utils'

export default {
  components: {
    CommunityListTable
  },
  beforeCreate: function() {
    this.$store.dispatch('getCommunities')
  },
  created: function() {
    utils.setTitle(this.$t('nav.communities'))
  },
  data() {
    return {
      searchQuery: ''
    }
  },
  beforeDestroy: function() {
    this.$store.dispatch('clearCommunities')
  },
  computed: {
    filteredCommunities() {
      if (!this.communities) {
        return null
      }
      
      if (!this.searchQuery || this.searchQuery.trim() === '') {
        return this.communities
      }
      
      const query = this.searchQuery.toLowerCase().trim()
      return this.communities.filter(community => {
        return (
          (community.name && community.name.toLowerCase().includes(query)) ||
          (community.tag && community.tag.toLowerCase().includes(query)) ||
          (community.slug && community.slug.toLowerCase().includes(query))
        )
      })
    },
    communities() {
      return this.$store.getters.communities
    },
    communityListPageCount() {
      return this.$store.getters.communityListPageCount
    },
    loggedIn() {
      return this.$store.getters.loggedIn
    },
    canCreateCommunity() {
      return this.loggedIn && this.$acl.can(['admin.community'])
    }
  },
  methods: {
    communityListPaginate(page) {
      this.$store.dispatch('getCommunities', { page })
    },
    communitySelected(item) {
      this.$router.push({ name: 'communityDetails', params: {communitySlug: item.value.slug}})
    }
  }
}
</script>
