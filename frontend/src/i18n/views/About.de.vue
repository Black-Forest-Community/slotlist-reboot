<template>
  <b-jumbotron header="Über slotlist.online">
    <p class="text-justify">
      <router-link :to="{name: 'home'}">slotlist.online</router-link> ist ein Missionsplanungs- und Slotlist-Verwaltungssystem für die ArmA-Community. Die Plattform vereinfacht die Erstellung und Verwaltung von Missionen und bietet allen Benutzern mit nur einem Steam-Account einfachen Zugang.
      <br>
      <br>Ursprünglich von <a href="https://github.com/MorpheusXAUT">MorpheusXAUT</a> entwickelt, wird das Projekt nun von Black Forest als Open-Source-Lösung für die ArmA-Community gepflegt und weiterentwickelt.
      <br>
      <br>Dieser Service wird kostenlos angeboten. Während wir hohe Verfügbarkeit und Zuverlässigkeit anstreben, wird der Service ohne Garantien bereitgestellt. Wir freuen uns über Feedback und Verbesserungsvorschläge zur Verbesserung der Plattform.
    </p>
    <h4>Entwicklung</h4>
    <p class="text-justify">
      <router-link :to="{name: 'home'}">slotlist.online</router-link> wird aktuell von Black Forest entwickelt.
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
      Die Repositories sowie deren Fehler-Tracker können außerdem dazu verwenden werden, um etwaige Bugs zu melden - alternativ kann dies über eine der unten genannten Kontaktmöglichkeiten geschehen.
    </p>
    <h4>Kontaktiere uns</h4>
    <p class="text-justify">
      Sollten irgendwelche Probleme oder Fehler auftreten oder solltest du Vorschläge for unsere Seite haben, dann:
      <dl class="row">
        <dt class="col-sm-3">öffne einen Fehlerbericht auf GitHub</dt>
        <dd class="col-sm-9">
          <a href="https://github.com/Black-Forest-Community/slotlist-reboot/issues">Fehler-Tracker</a>
        </dd>
        <dt class="col-sm-3">schick uns eine Email</dt>
        <dd class="col-sm-9">
          <a href="mailto:hello@slotlist.online?subject=slotlist.online - Hallo!">hello@slotlist.online</a>
        </dd>
      </dl>
      Kontakt-Details für rechtliche Anfrangen können im
      <router-link :to="{name: 'imprint'}">Impressum</router-link> gefunden werden.
    </p>
    <h4>Spezielle Danksagungen</h4>
    <p>
      Dieses Projekt baut auf der exzellenten Grundlage auf, die von <a href="https://github.com/MorpheusXAUT">MorpheusXAUT</a> geschaffen wurde, sowie auf der Unterstützung der ArmA-Community. Besonderen Dank an alle Mitwirkenden und Tester, die slotlist.online über die Jahre geholfen haben, sich zu verbessern.
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
