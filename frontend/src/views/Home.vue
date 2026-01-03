<template>
  <div>
    <!-- Show landing page for unauthenticated users -->
    <landing v-if="!$store.getters.loggedIn"></landing>

    <!-- Show normal home for authenticated users -->
    <template v-else>
      <home-de v-if="$i18n.locale === 'de' || $i18n.locale === 'de-at'"></home-de>
      <home-en v-else></home-en>
      <!-- Only show calendar if user has a community -->
      <calendar v-if="user && user.community"></calendar>
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
  computed: {
    user() {
      return this.$store.getters.user
    }
  },
  created: function() {
    utils.clearTitle()

    // Redirect to community application gate if logged in but no community
    if (this.$store.getters.loggedIn && (!this.user || !this.user.community)) {
      this.$router.push({ name: 'communityApplicationGate' })
    }
  }
}
</script>
