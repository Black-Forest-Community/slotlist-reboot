<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="m-0">{{ $t('nav.missions') }}</h2>
      <div style="max-width: 300px; flex: 1; margin-left: 2rem;">
        <input 
          type="search" 
          class="form-control" 
          v-model="searchQuery" 
          :placeholder="$t('mission.list.search')"
        />
      </div>
    </div>
    
    <mission-list-table v-if="filteredMissions" :missions-override="filteredMissions"></mission-list-table>
    <nav v-show="missionsPageCount > 1">
      <paginate ref="missionsPaginate" :pageCount="missionsPageCount" :initial-page="0" :clickHandler="missionsPaginate" :container-class="'pagination justify-content-center'" :page-class="'page-item'" :page-link-class="'page-link'" :prev-class="'page-item'" :prev-link-class="'page-link'" :next-class="'page-item'" :next-link-class="'page-link'"></paginate>
    </nav>
    <div class="small" v-html="$t('mission.timezone', { timezone: timezone })"></div>
    <div class="small">
      <b-form-group :label="$t('mission.list.filter')" label-for="missionListFilter">
        <div role="group" id="missionListFilter">
          <b-form-checkbox v-model="missionListFilter" name="ended" value="ended">
            {{ $t('mission.list.filter.ended') }}
          </b-form-checkbox>
          <b-form-checkbox v-if="loggedIn" v-model="missionListFilter" name="assigned" value="assigned">
            {{ $t('mission.list.filter.assigned') }}
          </b-form-checkbox>
          <b-form-checkbox v-if="loggedIn" v-model="missionListFilter" name="registered" value="registered">
            {{ $t('mission.list.filter.registered') }}
          </b-form-checkbox>
        </div>
        <div role="group" id="missionListRequiredDLCsFilter" v-if="haveMissionsAnyRequiredDLCs || (missionListRequiredDLCsFilter && missionListRequiredDLCsFilter.length > 0)">
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="aow" value="aow">
            <img src="/static/img/dlc-icons/aow.png" width="16px" alt="Art of War" /> {{ $t('mission.requiredDLCs.aow') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="apex" value="apex">
            <img src="/static/img/dlc-icons/apex.png" width="16px" alt="Apex" /> {{ $t('mission.requiredDLCs.apex') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="contact" value="contact">
            <img src="/static/img/dlc-icons/contact.png" width="16px" alt="Contact" /> {{ $t('mission.requiredDLCs.contact') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="csla" value="csla">
            <img src="/static/img/dlc-icons/csla.png" width="16px" alt="CSLA Iron Curtain" /> {{ $t('mission.requiredDLCs.csla') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="ef" value="ef">
            <img src="/static/img/dlc-icons/ef.png" width="16px" alt="Expeditionary Forces" /> {{ $t('mission.requiredDLCs.ef') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="gm" value="gm">
            <img src="/static/img/dlc-icons/gm.png" width="16px" alt="Global Mobilization" /> {{ $t('mission.requiredDLCs.gm') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="helicopters" value="helicopters">
            <img src="/static/img/dlc-icons/helicopters.png" width="16px" alt="Helicopters" /> {{ $t('mission.requiredDLCs.helicopters') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="jets" value="jets">
            <img src="/static/img/dlc-icons/jets.png" width="16px" alt="Jets" /> {{ $t('mission.requiredDLCs.jets') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="karts" value="karts">
            <img src="/static/img/dlc-icons/karts.png" width="16px" alt="Karts" /> {{ $t('mission.requiredDLCs.karts') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="laws-of-war" value="laws-of-war">
            <img src="/static/img/dlc-icons/lawsofwar.png" width="16px" alt="Laws of War" /> {{ $t('mission.requiredDLCs.laws-of-war') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="marksmen" value="marksmen">
            <img src="/static/img/dlc-icons/marksmen.png" width="16px" alt="Marksmen" /> {{ $t('mission.requiredDLCs.marksmen') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="tac-ops" value="tac-ops">
            <img src="/static/img/dlc-icons/tacops.png" width="16px" alt="Tac-Ops" /> {{ $t('mission.requiredDLCs.tac-ops') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="rf" value="rf">
            <img src="/static/img/dlc-icons/rf.png" width="16px" alt="Reaction Forces" /> {{ $t('mission.requiredDLCs.rf') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="tanks" value="tanks">
            <img src="/static/img/dlc-icons/tanks.png" width="16px" alt="Tanks" /> {{ $t('mission.requiredDLCs.tanks') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="vn" value="vn">
            <img src="/static/img/dlc-icons/vn.png" width="16px" alt="S.O.G. Prairie Fire" /> {{ $t('mission.requiredDLCs.vn') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="spe" value="spe">
            <img src="/static/img/dlc-icons/spe.png" width="16px" alt="Spearhead 1944" /> {{ $t('mission.requiredDLCs.spe') }}
          </b-form-checkbox>
          <b-form-checkbox v-model="missionListRequiredDLCsFilter" name="ws" value="ws">
            <img src="/static/img/dlc-icons/ws.png" width="16px" alt="Western Sahara" /> {{ $t('mission.requiredDLCs.ws') }}
          </b-form-checkbox>
        </div>
      </b-form-group>
    </div>
    <div class="text-center">
      <router-link tag="button" v-show="loggedIn" type="button" class="btn btn-success" :to="{name: 'missionCreator'}">
        <i class="fa fa-plus" aria-hidden="true"></i> {{ $t('button.create.mission') }}
      </router-link>
      <b-btn :disabled="refreshingMissions" @click="missionsPaginate(1)">
        <i class="fa fa-refresh" :class="{'fa-spin': refreshingMissions}" aria-hidden="true"></i> {{ $t('button.refresh') }}
      </b-btn>
    </div>
  </div>
</template>

<script>
import * as _ from 'lodash'
import MissionListTable from '../components/missions/MissionListTable.vue'
import utils from '../utils'

export default {
  components: {
    MissionListTable
  },
  beforeCreate: function() {
    if (_.isNil(this.$store.getters.missions) || _.isEmpty(this.$store.getters.missions)) {
      this.$store.dispatch('getMissions', { autoRefresh: true })
    }
  },
  created: function() {
    this.missionListFilter = this.$store.getters.missionListFilter
    this.missionListRequiredDLCsFilter = this.$store.getters.missionListRequiredDLCsFilter

    utils.setTitle(this.$t('nav.missions'))
  },
  data() {
    return {
      missionListFilter: [],
      missionListRequiredDLCsFilter: [],
      searchQuery: ''
    }
  },
  computed: {
    filteredMissions() {
      if (!this.missions) {
        return null
      }
      
      if (!this.searchQuery || this.searchQuery.trim() === '') {
        return this.missions
      }
      
      const query = this.searchQuery.toLowerCase().trim()
      return this.missions.filter(mission => {
        return (
          (mission.title && mission.title.toLowerCase().includes(query)) ||
          (mission.slug && mission.slug.toLowerCase().includes(query)) ||
          (mission.community && mission.community.name && mission.community.name.toLowerCase().includes(query)) ||
          (mission.community && mission.community.tag && mission.community.tag.toLowerCase().includes(query))
        )
      })
    },
    haveMissionsAnyRequiredDLCs() {
      if (_.isNil(this.missions)) {
        return false
      }

      return _.some(this.missions, (mission) => {
        return !_.isEmpty(mission.requiredDLCs)
      })
    },
    loggedIn() {
      return this.$store.getters.loggedIn
    },
    missions() {
      return this.$store.getters.missions
    },
    missionsPageCount() {
      return this.$store.getters.missionsPageCount
    },
    refreshingMissions() {
      return this.$store.getters.refreshingMissions
    },
    timezone() {
      return this.$store.getters.timezone
    }
  },
  methods: {
    missionSelected(item) {
      this.$router.push({ name: 'missionDetails', params: {missionSlug: item.value.slug}})
    },
    missionsPaginate(page) {
      this.$store.dispatch('getMissions', { page, autoRefresh: true })
    }
  },
  watch: {
    missionListFilter(val) {
      this.$store.dispatch('filterMissionList', val)
    },
    missionListRequiredDLCsFilter(val) {
      this.$store.dispatch('filterMissionListRequiredDLCs', val)
    }
  }
}
</script>
