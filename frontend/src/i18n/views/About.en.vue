<template>
  <b-jumbotron header="About slotlist.online">
    You play Arma and need a tool to manage your slotlists? Write us an <a href="mailto:hello@slotlist.online">an email</a>!
  </b-jumbotron>
</template>

<script>
import * as _ from 'lodash'

export default {
  computed: {
    backendVersion() {
      if (_.isNil(this.$store.getters.backendVersion)) {
        return null
      }

      return _.startsWith(this.$store.getters.backendVersion, 'v') ? this.$store.getters.backendVersion : `v${this.$store.getters.backendVersion}`
    },
    frontendVersion() {
      return _.startsWith(process.env.FRONTEND_VERSION, 'v') ? process.env.FRONTEND_VERSION : `v${process.env.FRONTEND_VERSION}`
    }
  }
}
</script>
