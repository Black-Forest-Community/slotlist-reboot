<template>
  <b-jumbotron header="About slotlist.online">
    <p class="text-justify">
      <router-link :to="{name: 'home'}">slotlist.online</router-link> is a mission planning and slotlist management system for the ArmA community. The platform simplifies mission creation and management, providing easy access to all users with just a Steam account.
      <br>
      <br>Originally created by <a href="https://github.com/MorpheusXAUT">MorpheusXAUT</a>, the project is now maintained and developed by Black Forest as an open-source solution for the ArmA community.
      <br>
      <br>This service is provided free of charge. While we strive for high availability and reliability, the service is provided as-is without guarantees. We welcome your feedback and suggestions to help improve the platform.
    </p>
    <h4>Development</h4>
    <p class="text-justify">
      <router-link :to="{name: 'home'}">slotlist.online</router-link> is currently developed by Black Forest.
      <dl class="row">
        <dd class="col-9">
          <span v-show="frontendVersion">{{ frontendVersion }}</span>
        </dd>
        <dt class="col-1">Source Code</dt>
        <dd class="col-2">
          <a href="https://github.com/Black-Forest-Community/slotlist-reboot">
            <i class="fa fa-github" aria-hidden="true"></i> slotlist-reboot</a>
        </dd>
        <dd class="col-9">
          <span v-show="backendVersion">{{ backendVersion }}</span>
        </dd>
      </dl>
      You can also use these repositories and their respective issue trackers to report any bugs you encounter - or use one of the contact methods available, as mentioned below.
    </p>
    <h4>Contact us</h4>
    <p class="text-justify">
      Should you run into any issues or bugs or have a suggestion for our site, feel free to:
      <dl class="row">
        <dt class="col-sm-3">open an issue on GitHub</dt>
        <dd class="col-sm-9">
          <a href="https://github.com/Black-Forest-Community/slotlist-reboot/issues">issue tracker</a>
        </dd>
        <dt class="col-sm-3">email us directly</dt>
        <dd class="col-sm-9">
          <a href="mailto:hello@slotlist.online?subject=slotlist.online - Hello!">hello@slotlist.online</a>
        </dd>
      </dl>
      Contact details for legal inquiries can be found on the
      <router-link :to="{name: 'imprint'}">imprint</router-link>.
    </p>
    <h4>Special thanks &amp; credits</h4>
    <p>
      This project builds on the excellent foundation created by <a href="https://github.com/MorpheusXAUT">MorpheusXAUT</a> and the support of the ArmA community. Special thanks to all contributors and testers who have helped improve slotlist.online over the years.
    </p>
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
