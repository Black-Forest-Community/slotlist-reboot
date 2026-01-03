<template>
  <div class="calendar-agenda">
    <div v-if="upcomingMissions.length === 0" class="text-center text-muted p-4">
      {{ $t('calendar.noUpcomingMissions') }}
    </div>
    <div v-else>
      <div v-for="group in groupedMissions" :key="group.date" class="agenda-day-group">
        <div class="agenda-date-header">
          <strong>{{ formatDateHeader(group.date) }}</strong>
        </div>
        <div class="agenda-mission-list">
          <div v-for="mission in group.missions" :key="mission.uid" class="agenda-mission-item">
            <router-link :to="{ name: 'missionDetails', params: { missionSlug: mission.slug }}" class="agenda-mission-link">
              <div class="agenda-mission-time">
                {{ formatTime(mission.startTime) }}
              </div>
              <div class="agenda-mission-details">
                <div class="agenda-mission-title">{{ mission.title }}</div>
                <div class="agenda-mission-community" v-if="mission.community">
                  <span v-if="mission.community.tag" class="community-tag">[{{ mission.community.tag }}]</span>
                  {{ mission.community.name }}
                </div>
              </div>
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import moment from 'moment-timezone'

export default {
  computed: {
    missions() {
      return this.$store.getters.missionsForAgenda
    },
    timezone() {
      return this.$store.getters.timezone
    },
    upcomingMissions() {
      if (_.isNil(this.missions) || _.isEmpty(this.missions)) {
        return []
      }

      const now = moment()
      return _.chain(this.missions)
        .filter(mission => moment(mission.startTime).isSameOrAfter(now, 'day'))
        .sortBy(mission => moment(mission.startTime).valueOf())
        .value()
    },
    groupedMissions() {
      return _.chain(this.upcomingMissions)
        .groupBy(mission => moment(mission.startTime).format('YYYY-MM-DD'))
        .map((missions, date) => ({
          date,
          missions
        }))
        .value()
    }
  },
  beforeMount() {
    this.loadAgendaMissions()
  },
  activated() {
    this.loadAgendaMissions()
  },
  methods: {
    formatDateHeader(dateString) {
      const date = moment(dateString)
      const today = moment().startOf('day')
      const tomorrow = moment().add(1, 'day').startOf('day')

      if (date.isSame(today, 'day')) {
        return this.$t('calendar.today')
      } else if (date.isSame(tomorrow, 'day')) {
        return this.$t('calendar.tomorrow')
      } else {
        return date.format('dddd, D. MMMM YYYY')
      }
    },
    formatTime(timestamp) {
      return moment(timestamp).tz(this.timezone).format('HH:mm')
    },
    loadAgendaMissions() {
      // Only load missions if user has a community
      const user = this.$store.getters.user
      const hasCommunity = user && user.community

      if (hasCommunity) {
        this.$store.dispatch('getMissionsForAgenda', {
          autoRefresh: true
        })
      }
    }
  }
}
</script>

<style scoped>
.calendar-agenda {
  margin-top: 20px;
}

.agenda-day-group {
  margin-bottom: 24px;
}

.agenda-date-header {
  padding: 12px 16px;
  background-color: #f8f9fa;
  border-left: 4px solid #367016;
  margin-bottom: 8px;
  font-size: 1.1em;
}

.agenda-mission-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.agenda-mission-item {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: #ffffff;
  transition: box-shadow 0.2s ease;
}

.agenda-mission-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.agenda-mission-link {
  display: flex;
  padding: 12px 16px;
  text-decoration: none;
  color: inherit;
  gap: 16px;
  align-items: center;
}

.agenda-mission-time {
  font-weight: bold;
  color: #367016;
  font-size: 1.1em;
  min-width: 60px;
  flex-shrink: 0;
}

.agenda-mission-details {
  flex: 1;
}

.agenda-mission-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.agenda-mission-community {
  font-size: 0.9em;
  color: #666;
}

.community-tag {
  font-weight: 600;
  margin-right: 6px;
  color: #367016;
}
</style>
