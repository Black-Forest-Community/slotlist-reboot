<template>
  <b-jumbotron header="Über slotlist.online">
    Ihr spielt Arma und braucht ein Tool um eure Slotlists zu verwalten? Schreibt uns <a href="mailto:hello@slotlist.online">eine E-Mail</a>!
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
