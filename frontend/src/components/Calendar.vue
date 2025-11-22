<template>
  <div class="row">
    <div class="col-sm-12">
      <div class="card">
        <div class="card-header">
          <h3>{{ currentMonth }}</h3>
        </div>
        <div class="card-block">
          <calendar-community-filter></calendar-community-filter>
          <div class="calendar-view-desktop">
            <calendar-header></calendar-header>
            <calendar-body></calendar-body>
          </div>
          <div class="calendar-view-mobile">
            <calendar-agenda></calendar-agenda>
          </div>
          <div class="small text-center" v-html="$t('mission.timezone', { timezone: timezone })"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import moment from 'moment-timezone'
import CalendarBody from './calendar/CalendarBody.vue'
import CalendarHeader from './calendar/CalendarHeader.vue'
import CalendarAgenda from './calendar/CalendarAgenda.vue'
import CalendarCommunityFilter from './calendar/CalendarCommunityFilter.vue'

export default {
  components: {
    CalendarBody,
    CalendarHeader,
    CalendarAgenda,
    CalendarCommunityFilter
  },
  beforeCreate: function() {
    if (_.isNil(this.$store.getters.missionsForCalendar)) {
      this.$store.dispatch('changeMissionCalendarCurrentMonth', moment().startOf('month'))
    }
  },
  computed: {
    currentMonth() {
      const month = this.$store.getters.missionCalendarCurrentMonth
      if (month) {
        return month.locale(this.$i18n.locale).format('MMMM YYYY')
      }
      return ''
    },
    loggedIn() {
      return this.$store.getters.loggedIn
    },
    timezone() {
      return this.$store.getters.timezone
    }
  }
}
</script>

<style scoped>
.calendar-view-desktop {
  display: none;
}

.calendar-view-mobile {
  display: block;
}

@media (min-width: 768px) {
  .calendar-view-desktop {
    display: block;
  }
  
  .calendar-view-mobile {
    display: none;
  }
}
</style>
