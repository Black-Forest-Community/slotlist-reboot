<template>
  <div id="app">
    <nav class="navbar navbar-toggleable-md navbar-light bg-faded mb-3">
      <button class="navbar-toggler navbar-toggler-right" type="button" @click="navbarCollapsed = !navbarCollapsed" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <router-link class="navbar-brand" :to="{name:'home'}">slotlist.online</router-link>
      <div class="collapse navbar-collapse" :class="{'show': !navbarCollapsed}" id="navbarSupportedContent" @click="closeNavbar">
        <ul class="navbar-nav mr-auto">
          <li class="nav-item">
            <router-link class="nav-link" :to="{name:'home'}" exact @click.native="closeNavbar">
              <i class="fa fa-home" aria-hidden="true"></i> {{ $t('nav.home') }}
            </router-link>
          </li>
          <li class="nav-item" v-if="loggedIn && user && user.community">
            <router-link class="nav-link" :to="{name:'missionList'}" @click.native="closeNavbar">
              <i class="fa fa-tasks" aria-hidden="true"></i> {{ $t('nav.missions') }}
            </router-link>
          </li>
          <li class="nav-item" v-if="loggedIn && user && user.community">
            <router-link class="nav-link" :to="{name:'missionSlotTemplateList'}" @click.native="closeNavbar">
              <i class="fa fa-file-text-o" aria-hidden="true"></i> {{ $t('nav.missionSlotTemplates') }}
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" :to="{name:'communityList'}" @click.native="closeNavbar">
              <i class="fa fa-users" aria-hidden="true"></i> {{ $t('nav.communities') }}
            </router-link>
          </li>
          <li class="nav-item" v-if="loggedIn && user && user.community">
            <router-link class="nav-link" :to="{name:'userList'}" @click.native="closeNavbar">
              <i class="fa fa-user" aria-hidden="true"></i> {{ $t('nav.users') }}
            </router-link>
          </li>
        </ul>
        <ul class="navbar-nav">
          <li class="nav-item" v-if="loggedIn">
            <router-link class="nav-link" :class="{'text-danger': unseenNotificationCount > 0, 'font-weight-bold': unseenNotificationCount > 0}" :to="{name:'notificationList'}" @click.native="closeNavbar">
              <i class="fa fa-bell" aria-hidden="true"></i> {{ unseenNotificationCount }} {{ $t('nav.notifications') }}
            </router-link>
          </li>
          <li class="nav-item" v-if="loggedIn">
            <router-link class="nav-link" :to="{name:'account'}" @click.native="closeNavbar">
              <i class="fa fa-user" aria-hidden="true"></i> {{ $t('nav.account') }}
            </router-link>
          </li>
          <li class="nav-item" v-if="!loggedIn">
            <router-link class="nav-link text-primary" :to="{name:'login'}" @click.native="closeNavbar">
              <i class="fa fa-sign-in" aria-hidden="true"></i> {{ $t('nav.login') }}
            </router-link>
          </li>
          <li class="nav-item" v-if="loggedIn">
            <a class="nav-link text-danger" href="#" @click.prevent="logout">
              <i class="fa fa-sign-out" aria-hidden="true"></i> {{ $t('nav.logout') }}
            </a>
          </li>
          <b-nav-item-dropdown class="text-muted" right no-caret>
            <template slot="button-content">
              <span v-html="selectedLanguage"></span>
            </template>
            <b-dropdown-item @click="setLocale('en')"><img src="/img/flags/gb.png"> English</b-dropdown-item>
            <b-dropdown-item @click="setLocale('de')"><img src="/img/flags/de.png"> Deutsch</b-dropdown-item>
            <b-dropdown-item @click="setLocale('de-at')"><img src="/img/flags/at.png"> Österreichisch</b-dropdown-item>
          </b-nav-item-dropdown>
        </ul>
      </div>
    </nav>
    <template>
      <div class="container">
        <b-alert :variant="alertVariant" :dismissible="alertDismissible" :show="showAlert" @dismissed="alertDismissed" @dismiss-count-down="alertDismissCountDown">
          <div v-html="alertMessage"></div>
        </b-alert>
        <router-view></router-view>
        <div v-show="working">
          <loading-overlay :message="working"></loading-overlay>
        </div>
      </div>
    </template>
    <footer class="footer">
      <div class="container">
        <div class="row">
          <div class="col">
            <span class="text-muted small float-left">
              Copyright &copy; 2017-{{ year }}
              <router-link to="/">slotlist.online</router-link>. {{ $t('rights.reserved') }}.
            </span>
          </div>
          <div class="col text-center">
            <span class="text-muted small">
              Forked with
              <i class="fa fa-heart" aria-hidden="true"></i> by Black Forest
            </span>
          </div>
          <div class="col">
            <span class="text-muted small float-right">
              <router-link to="/faq">{{ $t('nav.faq') }}</router-link> |
              <router-link to="/about">{{ $t('nav.about') }}</router-link> |
              <router-link to="/imprint">{{ $t('nav.imprint') }}</router-link> |
              <router-link to="/privacy">{{ $t('nav.privacy') }}</router-link> |
              <a href="https://github.com/Black-Forest-Community/slotlist-reboot">
                <i class="fa fa-github"></i> Source Code</a> |
            </span>
          </div>
        </div>
      </div>
    </footer>
    <button class="dark-mode-toggle" @click="toggleDarkMode" :title="darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'">
      <i class="fa" :class="darkMode ? 'fa-sun-o' : 'fa-moon-o'"></i>
    </button>
  </div>
</template>

<script>
import * as _ from 'lodash'
import moment from 'moment-timezone'

import utils from '../utils'
import { pendingRequestCount } from '../api/util'

export default {
  beforeCreate: function() {
    let locale = this.$ls.get('locale')
    if (_.isNil(locale) || !_.isString(locale) || _.isEmpty(locale)) {
      console.info('Locale not defined, retrieving from browser language')

      const userLanguage = navigator.language || navigator.userLanguage || navigator.browserLanguage || navigator.systemLanguage;
      locale = userLanguage.split('-')[0].trim()

      if (!_.isString(locale) || _.isEmpty(locale)) {
        console.info('Failed to get user language from browser, falling back to English')
        locale = 'en'
      }
    }

    this.$store.dispatch('setLocale', locale)

    let timezone = this.$ls.get('timezone')
    if (_.isNil(timezone) || !_.isString(timezone) || _.isEmpty(timezone)) {
      console.info('Timezone not defined, guessing from browser settings')

      timezone = moment.tz.guess()

      if (!_.isString(timezone) || _.isEmpty(timezone)) {
        console.info('Failed to get user timezone from browser, falling back to UTC')
        timezone = 'Etc/UTC'
      }
    }

    this.$store.dispatch('setTimezone', timezone)

    const darkMode = this.$ls.get('dark-mode')
    if (darkMode === 'true') {
      document.documentElement.setAttribute('data-theme', 'dark')
    } else if (darkMode === null || darkMode === undefined) {
      // Auto-detect from browser preference if user hasn't set a preference
      const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      if (prefersDark) {
        document.documentElement.setAttribute('data-theme', 'dark')
        this.$ls.set('dark-mode', 'true')
      }
    }

    const token = this.$ls.get('auth-token')
    if (!_.isNil(token)) {
      this.$store.dispatch('setTokenFromLocalStorage', token)
        .then(() => {
          // need to check for token again since an expired token is cleared during the `setTokenFromLocalStorage` action,
          // leading to an instant authentication error if the users loads the app after the token expired
          if (!_.isNil(this.$ls.get('auth-token'))) {
            const lastRefreshedAt = this.$ls.get('auth-token-last-refreshed')
            if (_.isNil(lastRefreshedAt) || moment(lastRefreshedAt) <= moment().subtract(1, 'hour')) {
              this.performInitialTokenRefresh()
            }

            if (!this.$store.getters.pollingUnseenNotifications) {
              this.$store.dispatch('getUnseenNotificationCount', { autoRefresh: true })
            }
          }
        })
    }
  },
  created: function() {
    utils.clearTitle()
  },
  beforeDestroy: function() {
    this.dispatch('clearMissions')
  },
  data() {
    const savedDarkMode = this.$ls.get('dark-mode')
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
    const darkMode = savedDarkMode === 'true' || (savedDarkMode === null && prefersDark)
    
    return {
      initialTokenRefresh: true,
      navbarCollapsed: true,
      darkMode: darkMode
    }
  },
  computed: {
    alertDismissible() {
      return this.$store.getters.alertDismissible
    },
    alertMessage() {
      return this.$store.getters.alertMessage
    },
    alertVariant() {
      return this.$store.getters.alertVariant
    },
    loggedIn() {
      return this.$store.getters.loggedIn
    },
    user() {
      return this.$store.getters.user
    },
    selectedLanguage() {
      const locale = this.$i18n.locale

      switch (locale) {
        case 'en': return '<img src="/img/flags/gb.png"> English'
        case 'de': return '<img src="/img/flags/de.png"> Deutsch'
        case 'de-at': return '<img src="/img/flags/at.png"> Österreichisch'
        default: return '<i class="fa fa-language" aria-hidden="true"> Language'
      }
    },
    showAlert() {
      return this.$store.getters.showAlert
    },
    unseenNotificationCount() {
      return this.$store.getters.unseenNotificationCount
    },
    working() {
      return this.$store.getters.working
    },
    year() {
      return new Date().getFullYear()
    }
  },
  methods: {
    alertDismissCountDown(val) {
      if (val === 1) {
        console.info('This is gonna look ugly...')
        this.$store.dispatch('clearAlert')
      }
    },
    alertDismissed() {
      this.$store.dispatch('clearAlert')
    },
    closeNavbar() {
      this.navbarCollapsed = true
    },
    logout() {
      this.closeNavbar()
      this.$store.dispatch('performLogout')
        .then(() => {
          this.$router.push({ path: '/', query: { logout: true } })
        })
    },
    performInitialTokenRefresh() {
      if (this.initialTokenRefresh) {
        if (pendingRequestCount() > 0) {
          setTimeout(this.performInitialTokenRefresh, 5000)
          return
        }

        this.initialTokenRefresh = false

        this.$store.dispatch('refreshToken', { silent: true })
      }
    },
    setLocale(locale) {
      this.$store.dispatch('setLocale', locale)
    },
    toggleDarkMode() {
      this.darkMode = !this.darkMode
      const theme = this.darkMode ? 'dark' : 'light'
      document.documentElement.setAttribute('data-theme', theme)
      this.$ls.set('dark-mode', this.darkMode.toString())
    }
  }
}
</script>
