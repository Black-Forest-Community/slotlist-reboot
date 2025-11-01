<template>
  <div>
    <mission-slotlist-group v-for="missionSlotGroup in missionSlotGroups" :missionSlotGroup="missionSlotGroup" :key="missionSlotGroup.uid"></mission-slotlist-group>
    <div class="text-center">
      <b-btn variant="success" v-if="isMissionEditor && !hasMissionEnded" v-b-modal.missionSlotGroupCreateModal>
        <i class="fa fa-plus" aria-hidden="true"></i> {{ $t('button.create.mission.slotGroup') }}
      </b-btn>
      <b-btn variant="success" v-if="isMissionEditor && !hasMissionEnded" v-b-modal.missionApplySlotTemplateModal>
        <i class="fa fa-file-text-o" aria-hidden="true"></i> {{ $t('button.apply.mission.slotGroup') }}
      </b-btn>
      <b-btn @click="refreshMissionSlotlist">
        <i class="fa fa-refresh" aria-hidden="true"></i> {{ $t('button.refresh') }}
      </b-btn>
    </div>
    <div v-if="isMissionEditor && !hasMissionEnded">
      <br>
      <div class="small text-muted text-center" v-html="anyMissionSlotSelected ? $tc('mission.slot.selection.actions', missionSlotSelectionCount, { count: missionSlotSelectionCount }) : $t('mission.slot.selection.hint')"></div>
      <br v-if="anyMissionSlotSelected">
      <div class="text-center" v-if="anyMissionSlotSelected">
        <b-btn variant="primary" v-b-modal.missionSlotSelectionEditModal>
          <i class="fa fa-edit" aria-hidden="true"></i> {{ $t('button.edit.mission.slot.selection') }}
        </b-btn>
        <click-confirm yes-icon="fa fa-close" yes-class="btn btn-warning" button-size="sm" :messages="{title: $t('mission.slot.confirm.unassign.selection'), yes: $t('button.confirm'), no: $t('button.cancel')}">
          <b-btn variant="warning" @click="unassignSelectedMissionSlots">
            <i class="fa fa-close" aria-hidden="true"></i> {{ $t('button.unassign.mission.slot.selection') }}
          </b-btn>
        </click-confirm>
        <click-confirm yes-icon="fa fa-trash" yes-class="btn btn-danger" button-size="sm" :messages="{title: $t('mission.slot.confirm.delete.selection'), yes: $t('button.confirm'), no: $t('button.cancel')}">
          <b-btn variant="danger" @click="deleteSelectedMissionSlots">
            <i class="fa fa-trash" aria-hidden="true"></i> {{ $t('button.delete.mission.slot.selection') }}
          </b-btn>
        </click-confirm>
        <b-btn variant="secondary" @click="clearMissionSlotSelection">
          <i class="fa fa-times-circle" aria-hidden="true"></i> {{ $t('button.clear.selection') }}
        </b-btn>
      </div>
    </div>
    <br v-if="hasMissionAnyRequiredDLCs">
    <div v-if="hasMissionAnyRequiredDLCs" class="text-center small text-muted">
      <img src="/static/img/dlc-icons/aow.png" width="12px" alt="Art of War" /> {{ $t('mission.requiredDLCs.aow') }} | 
      <img src="/static/img/dlc-icons/apex.png" width="12px" alt="Apex" /> {{ $t('mission.requiredDLCs.apex') }} | 
      <img src="/static/img/dlc-icons/contact.png" width="12px" alt="Contact" /> {{ $t('mission.requiredDLCs.contact') }} | 
      <img src="/static/img/dlc-icons/csla.png" width="12px" alt="CSLA Iron Curtain" /> {{ $t('mission.requiredDLCs.csla') }} | 
      <img src="/static/img/dlc-icons/ef.png" width="12px" alt="Expeditionary Forces" /> {{ $t('mission.requiredDLCs.ef') }} | 
      <img src="/static/img/dlc-icons/gm.png" width="12px" alt="Global Mobilization" /> {{ $t('mission.requiredDLCs.gm') }} | 
      <img src="/static/img/dlc-icons/helicopters.png" width="12px" alt="Helicopters" /> {{ $t('mission.requiredDLCs.helicopters') }} | 
      <img src="/static/img/dlc-icons/jets.png" width="12px" alt="Jets" /> {{ $t('mission.requiredDLCs.jets') }} | 
      <br/>
      <img src="/static/img/dlc-icons/karts.png" width="12px" alt="Karts" /> {{ $t('mission.requiredDLCs.karts') }} | 
      <img src="/static/img/dlc-icons/lawsofwar.png" width="12px" alt="Laws of War" /> {{ $t('mission.requiredDLCs.laws-of-war') }} | 
      <img src="/static/img/dlc-icons/marksmen.png" width="12px" alt="Marksmen" /> {{ $t('mission.requiredDLCs.marksmen') }} |
      <img src="/static/img/dlc-icons/rf.png" width="12px" alt="Reaction Forces" /> {{ $t('mission.requiredDLCs.rf') }} | 
      <br/>
      <img src="/static/img/dlc-icons/spe.png" width="12px" alt="Spearhead 1944" /> {{ $t('mission.requiredDLCs.spe') }} | 
      <img src="/static/img/dlc-icons/tacops.png" width="12px" alt="Tac-Ops" /> {{ $t('mission.requiredDLCs.tac-ops') }} | 
      <img src="/static/img/dlc-icons/tanks.png" width="12px" alt="Tanks" /> {{ $t('mission.requiredDLCs.tanks') }} | 
      <img src="/static/img/dlc-icons/vn.png" width="12px" alt="S.O.G. Prairie Fire" /> {{ $t('mission.requiredDLCs.vn') }} | 
      <img src="/static/img/dlc-icons/ws.png" width="12px" alt="Western Sahara" /> {{ $t('mission.requiredDLCs.ws') }}
    </div>
  </div>
</template>

<script>
import * as _ from 'lodash'
import moment from 'moment-timezone'
import MissionSlotlistGroup from './MissionSlotlistGroup.vue'

export default {
  components: {
    MissionSlotlistGroup
  },
  computed: {
    anyMissionSlotSelected() {
      return !_.isEmpty(this.$store.getters.missionSlotSelection)
    },
    hasMissionAnyRequiredDLCs() {
      if (_.isNil(this.missionDetails)) {
        return false
      }

      if (!_.isEmpty(this.missionDetails.requiredDLCs)) {
        return true
      }

      return _.some(this.missionSlotGroups, (slotGroup) => {
        return _.some(slotGroup.slots, (slot) => {
          return !_.isEmpty(slot.requiredDLCs)
        })
      })
    },
    hasMissionEnded() {
      if (_.isNil(this.missionDetails)) {
        return false
      }

      return moment().isAfter(moment(this.missionDetails.endTime))
    },
    isMissionEditor() {
      return this.$acl.can([`mission.${this.$route.params.missionSlug}.creator`, `mission.${this.$route.params.missionSlug}.editor`])
    },
    loggedIn() {
      return this.$store.getters.loggedIn
    },
    missionDetails() {
      return this.$store.getters.missionDetails
    },
    missionSlotGroups() {
      return this.$store.getters.missionSlotGroups
    },
    missionSlotSelectionCount() {
      return this.$store.getters.missionSlotSelection.length
    }
  },
  methods: {
    clearMissionSlotSelection() {
      this.$store.dispatch('clearMissionSlotSelection')
    },
    deleteSelectedMissionSlots() {
      this.$store.dispatch('deleteSelectedMissionSlots', { missionSlug: this.$route.params.missionSlug })
    },
    getMissionSlotTemplates() {
      this.$store.dispatch('getMissionSlotTemplates', { limit: 100 })
    },
    refreshMissionSlotlist() {
      this.$store.dispatch('getMissionSlotlist', { missionSlug: this.$route.params.missionSlug })
    },
    unassignSelectedMissionSlots() {
      this.$store.dispatch('unassignSelectedMissionSlots', { missionSlug: this.$route.params.missionSlug })
    }
  }
}
</script>

<style scoped>
.text-center {
  margin-bottom: 0.5rem;
}

.text-center .btn {
  margin: 0.5rem;
}

@media (max-width: 768px) {
  .text-center {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    margin-bottom: 0.5rem;
  }
  
  .text-center .btn {
    flex: 1 1 auto;
    min-width: 0;
    margin: 0;
    font-size: 0.875rem;
    padding: 0.375rem 0.75rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .text-center .click-confirm {
    flex: 1 1 auto;
    min-width: 0;
  }
  
  .text-center .click-confirm .btn {
    width: 100%;
  }
}
</style>
