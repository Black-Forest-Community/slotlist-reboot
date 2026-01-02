<template>
  <div>
    <!-- Show landing page for unauthenticated users -->
    <landing v-if="!$store.getters.loggedIn"></landing>

    <!-- Show normal home for authenticated users -->
    <template v-else>
      <home-de v-if="$i18n.locale === 'de' || $i18n.locale === 'de-at'"></home-de>
      <home-en v-else></home-en>
      <calendar></calendar>
    </template>
  </div>
</template>

<script>
import Calendar from '../components/Calendar.vue'
import Landing from './Landing.vue'
import HomeDe from '../i18n/views/Home.de.vue'
import HomeEn from '../i18n/views/Home.en.vue'
import utils from '../utils'

export default {
  components: {
    Calendar,
    Landing,
    HomeDe,
    HomeEn,
  },
  created: function() {
    utils.clearTitle()
  }
}
</script>
