<template>
  <div class="landing-page">
    <div class="jumbotron">
      <h1 class="display-4">{{ $t('landing.title') }}</h1>
      <p class="lead">
        {{ $t('landing.subtitle') }}
      </p>
      <hr class="my-4">
      <p>
        {{ $t('landing.description') }}
      </p>
      <div class="button-group">
        <router-link :to="{ name: 'login' }" class="btn btn-primary btn-lg">
          <i class="fa fa-steam"></i> {{ $t('landing.signInButton') }}
        </router-link>
        <router-link :to="{ name: 'communityList' }" class="btn btn-secondary btn-lg">
          <i class="fa fa-users"></i> {{ $t('landing.browseCommunities') }}
        </router-link>
      </div>
    </div>

    <div class="container">
      <div class="row">
        <div class="col-md-4 text-center mb-4">
          <i class="fa fa-users fa-3x mb-3 text-primary"></i>
          <h3>{{ $t('landing.feature1Title') }}</h3>
          <p>{{ $t('landing.feature1Description') }}</p>
        </div>
        <div class="col-md-4 text-center mb-4">
          <i class="fa fa-calendar fa-3x mb-3 text-primary"></i>
          <h3>{{ $t('landing.feature2Title') }}</h3>
          <p>{{ $t('landing.feature2Description') }}</p>
        </div>
        <div class="col-md-4 text-center mb-4">
          <i class="fa fa-list fa-3x mb-3 text-primary"></i>
          <h3>{{ $t('landing.feature3Title') }}</h3>
          <p>{{ $t('landing.feature3Description') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Landing',
  i18n: {
    messages: {
      en: {
        landing: {
          title: 'Welcome to Slotlist',
          subtitle: 'The mission planning and slot management system for ArmA 3 communities.',
          description: 'Sign in with Steam to browse communities and apply for membership.',
          signInButton: 'Sign in with Steam',
          browseCommunities: 'Browse Communities',
          feature1Title: 'Join a Community',
          feature1Description: 'Browse and apply to ArmA 3 communities to participate in organized missions.',
          feature2Title: 'Plan Missions',
          feature2Description: 'Create and manage missions with detailed slotlists and scheduling.',
          feature3Title: 'Manage Slots',
          feature3Description: 'Organize mission slots with DLC requirements, restrictions, and automatic assignment.'
        }
      },
      de: {
        landing: {
          title: 'Willkommen bei Slotlist',
          subtitle: 'Das Missionsplanungs- und Slot-Verwaltungssystem für ArmA 3-Communities.',
          description: 'Melde dich mit Steam an, um Communities zu durchsuchen und dich zu bewerben.',
          signInButton: 'Mit Steam anmelden',
          browseCommunities: 'Communities durchsuchen',
          feature1Title: 'Einer Community beitreten',
          feature1Description: 'Durchsuche ArmA 3-Communities und bewirb dich, um an organisierten Missionen teilzunehmen.',
          feature2Title: 'Missionen planen',
          feature2Description: 'Erstelle und verwalte Missionen mit detaillierten Slotlisten und Zeitplanung.',
          feature3Title: 'Slots verwalten',
          feature3Description: 'Organisiere Missions-Slots mit DLC-Anforderungen, Einschränkungen und automatischer Zuweisung.'
        }
      }
    }
  }
}
</script>

<style scoped>
.landing-page {
  margin-top: 2rem;
}

.jumbotron {
  background-color: #f8f9fa;
  padding: 4rem 2rem;
  border-radius: 0.3rem;
}

.display-4 {
  font-weight: 300;
}

.button-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1rem;
}

.button-group .btn {
  flex: 1 1 auto;
  min-width: 200px;
}

/* Mobile: stack buttons vertically and make full-width */
@media (max-width: 576px) {
  .button-group {
    flex-direction: column;
  }

  .button-group .btn {
    width: 100%;
    min-width: auto;
  }
}
</style>
