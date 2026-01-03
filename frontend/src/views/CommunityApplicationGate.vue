<template>
  <div class="container mt-5">
    <div class="card">
      <div class="card-body">
        <div v-if="loading" class="text-center">
          <i class="fa fa-spinner fa-spin fa-2x"></i>
          <p class="mt-3">{{ $t('gate.checking') }}</p>
        </div>

        <div v-else-if="hasPendingApplication" class="text-center">
          <i class="fa fa-clock-o fa-3x text-warning mb-3"></i>
          <h3>{{ $t('gate.pendingTitle') }}</h3>
          <p v-if="applicationCommunityName">
            {{ $t('gate.pendingMessage', { community: applicationCommunityName }) }}
          </p>
          <p v-else>
            {{ $t('gate.pendingMessageGeneric') }}
          </p>
          <p class="text-muted">
            {{ $t('gate.pendingExplanation') }}
          </p>
          <div class="mt-4">
            <router-link :to="{ name: 'communityList' }" class="btn btn-secondary">
              <i class="fa fa-users"></i> {{ $t('gate.browseCommunities') }}
            </router-link>
          </div>
        </div>

        <div v-else class="text-center">
          <i class="fa fa-user-plus fa-3x text-primary mb-3"></i>
          <h3>{{ $t('gate.noMembershipTitle') }}</h3>
          <p>
            {{ $t('gate.noMembershipMessage') }}
          </p>
          <p class="text-muted">
            {{ $t('gate.noMembershipExplanation') }}
          </p>
          <div class="mt-4">
            <router-link :to="{ name: 'communityList' }" class="btn btn-primary btn-lg">
              <i class="fa fa-users"></i> {{ $t('gate.browseCommunitiesAndApply') }}
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CommunityApplicationGate',
  data() {
    return {
      loading: true,
      hasPendingApplication: false,
      applicationCommunityName: null,
      pollInterval: null
    }
  },
  async mounted() {
    await this.checkStatus()

    // Poll for status updates every 30 seconds if pending
    if (this.hasPendingApplication) {
      this.pollInterval = setInterval(() => {
        this.checkStatus()
      }, 30000) // 30 seconds
    }
  },
  beforeDestroy() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval)
    }
  },
  methods: {
    async checkStatus() {
      try {
        // Refresh account details to get latest user info
        await this.$store.dispatch('getAccountDetails')

        const user = this.$store.getters.user

        // If user now has community, redirect to original destination
        if (user && user.community) {
          const redirect = this.$ls.get('auth-redirect')
          if (redirect) {
            this.$ls.remove('auth-redirect')
            this.$router.push(redirect)
          } else {
            this.$router.push({ path: '/missions' })
          }
          return
        }

        // Check for pending applications by trying all communities
        // This is a workaround since there's no global "my applications" endpoint
        const communitiesResponse = await this.$store.dispatch('getCommunities', {
          limit: 100,
          offset: 0
        })

        if (communitiesResponse && communitiesResponse.communities) {
          // Try to find pending applications
          for (const community of communitiesResponse.communities) {
            try {
              const status = await this.$store.dispatch('getCommunityApplicationStatus', {
                communitySlug: community.slug
              })

              if (status && status.application) {
                if (status.application.status === 'submitted') {
                  this.hasPendingApplication = true
                  this.applicationCommunityName = community.name
                  break
                }
              }
            } catch (err) {
              // No application for this community, continue
              continue
            }
          }
        }

        this.loading = false
      } catch (error) {
        console.error('Error checking application status:', error)
        this.loading = false
      }
    }
  },
  i18n: {
    messages: {
      en: {
        gate: {
          checking: 'Checking application status...',
          pendingTitle: 'Application Pending',
          pendingMessage: 'Your application to join {community} is currently pending approval.',
          pendingMessageGeneric: 'You have a pending community application.',
          pendingExplanation: "You'll be able to access missions and other content once your application is approved by the community leaders.",
          browseCommunities: 'Browse Communities',
          noMembershipTitle: 'Community Membership Required',
          noMembershipMessage: 'To access missions and full content, you need to be a member of a community.',
          noMembershipExplanation: 'Please browse available communities and submit an application to join one.',
          browseCommunitiesAndApply: 'Browse Communities & Apply'
        }
      },
      de: {
        gate: {
          checking: 'Bewerbungsstatus wird überprüft...',
          pendingTitle: 'Bewerbung ausstehend',
          pendingMessage: 'Deine Bewerbung für {community} wartet auf Genehmigung.',
          pendingMessageGeneric: 'Du hast eine ausstehende Community-Bewerbung.',
          pendingExplanation: 'Du kannst auf Missionen und andere Inhalte zugreifen, sobald deine Bewerbung von den Community-Leitern genehmigt wurde.',
          browseCommunities: 'Communities durchsuchen',
          noMembershipTitle: 'Community-Mitgliedschaft erforderlich',
          noMembershipMessage: 'Um auf Missionen und vollständige Inhalte zugreifen zu können, musst du Mitglied einer Community sein.',
          noMembershipExplanation: 'Bitte durchsuche verfügbare Communities und reiche eine Bewerbung ein, um einer beizutreten.',
          browseCommunitiesAndApply: 'Communities durchsuchen & bewerben'
        }
      }
    }
  }
}
</script>

<style scoped>
.card {
  max-width: 600px;
  margin: 0 auto;
}
</style>
