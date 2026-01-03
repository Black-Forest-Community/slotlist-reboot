import store from '../store'

/**
 * Check if user is authenticated
 * Redirects to login if not authenticated
 */
export function requireAuth(to, from, next) {
  if (!store.getters.loggedIn) {
    // Store redirect path
    store.dispatch('setRedirect', { path: to.fullPath })
    next({ name: 'login' })
  } else {
    next()
  }
}

/**
 * Check if user has an approved community membership
 * Redirects to login if not authenticated,
 * or to community application gate if no community
 */
export function requireCommunity(to, from, next) {
  if (!store.getters.loggedIn) {
    store.dispatch('setRedirect', { path: to.fullPath })
    return next({ name: 'login' })
  }

  const user = store.getters.user

  // If user has no community, redirect to community application gate
  // Store redirect so they can be sent here after community approval
  if (!user || !user.community) {
    store.dispatch('setRedirect', { path: to.fullPath })
    next({ name: 'communityApplicationGate' })
  } else {
    next()
  }
}
