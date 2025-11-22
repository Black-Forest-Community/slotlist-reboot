<template>
  <tr>
    <td v-html="formattedPermission"></td>
  </tr>
</template>

<script>
import * as _ from 'lodash'

export default {
  props: [
    'accountPermission'
  ],
  computed: {
    formattedPermission() {
      const permission = this.accountPermission.permission.toLowerCase()
      
      // Admin permissions
      if (permission === 'admin.community') {
        return `<span class="badge badge-danger">${this.$t('permission.admin.community')}</span>`
      } else if (permission === 'admin.mission') {
        return `<span class="badge badge-danger">${this.$t('permission.admin.mission')}</span>`
      } else if (permission === 'admin.slotlist') {
        return `<span class="badge badge-danger">${this.$t('permission.admin.slotlist')}</span>`
      } else if (permission === 'admin.user') {
        return `<span class="badge badge-danger">${this.$t('permission.admin.user')}</span>`
      }
      
      // Community permissions
      if (_.includes(permission, 'community.')) {
        const communitySlug = permission.split('.')[1]
        
        if (_.endsWith(permission, 'founder')) {
          return `<span class="badge badge-primary">${this.$t('community.permission.founder')}</span> - <strong>${communitySlug}</strong>`
        } else if (_.endsWith(permission, 'leader')) {
          return `<span class="badge badge-primary">${this.$t('community.permission.leader')}</span> - <strong>${communitySlug}</strong>`
        } else if (_.endsWith(permission, 'recruitment')) {
          return `<span class="badge badge-info">${this.$t('community.permission.recruitment')}</span> - <strong>${communitySlug}</strong>`
        }
      }
      
      // Mission permissions
      if (_.includes(permission, 'mission.')) {
        const missionSlug = permission.split('.')[1]
        
        if (_.endsWith(permission, 'creator')) {
          return `<span class="badge badge-success">${this.$t('mission.permission.creator')}</span> - <strong>${missionSlug}</strong>`
        } else if (_.endsWith(permission, 'editor')) {
          return `<span class="badge badge-success">${this.$t('mission.permission.editor')}</span> - <strong>${missionSlug}</strong>`
        }
      }
      
      // Fallback: show raw permission
      return `<span class="text-muted font-italic">${this.accountPermission.permission}</span>`
    }
  }
}
</script>
