<template>
  <div class="row">
    <div class="col-sm-4 text-center">
      <b-btn :disabled="refreshingMissionsForCalendar" @click="refreshCalendarMissions()">
        <i class="fa fa-refresh" :class="{'fa-spin': refreshingMissionsForCalendar}" aria-hidden="true"></i> {{ $t('button.refresh') }}
      </b-btn>
    </div>
    <div class="col-sm-8">
      <b-btn-group>
        <b-btn variant="primary" @click="changeMonth(-1)">
          <i class="fa fa-angle-left" aria-hidden="true"></i> {{ $t('calendar.month.previous') }}
        </b-btn>
        <b-btn variant="secondary" @click="changeMonth(0)">
          <i class="fa fa-angle-down" aria-hidden="true"></i> {{ $t('calendar.month.current') }}
        </b-btn>
        <b-btn variant="primary" @click="changeMonth(1)">
          {{ $t('calendar.month.next') }}
          <i class="fa fa-angle-right" aria-hidden="true"></i>
        </b-btn>
      </b-btn-group>
    </div>
  </div>
</template>

<script>
import moment from 'moment-timezone'

export default {
  computed: {
    currentMonth() {
      return this.$store.getters.missionCalendarCurrentMonth
    },
    refreshingMissionsForCalendar() {
      return this.$store.getters.refreshingMissionsForCalendar
    }
  },
  methods: {
    changeMonth(direction) {
      let payload;

      if (direction === 0) {
        payload = moment().startOf('month')
      } else if (direction < 0) {
        payload = moment(this.currentMonth).subtract(1, 'month').startOf('month')
      } else {
        payload = moment(this.currentMonth).add(1, 'month').startOf('month')
      }

      this.$store.dispatch('changeMissionCalendarCurrentMonth', payload)
    },
    refreshCalendarMissions() {
      this.$store.dispatch('getMissionsForCalendar', {
        autoRefresh: true,
        startDate: moment(this.currentMonth).startOf('month'),
        endDate: moment(this.currentMonth).endOf('month')
      })
    }
  }
}
</script>

<style>
