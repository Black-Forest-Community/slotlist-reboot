import axios from 'axios'

export const v1 = {
  deleteAccount(nickname) {
    return axios.post('/v1/auth/account/delete', { nickname })
  },
  getLoginRedirectUrl() {
    const returnUrl = `${window.location.origin}/login`
    return axios.get('/v1/auth/steam', { params: { return_url: returnUrl } })
  },
  performLogin(url) {
    return axios.post('/v1/auth/steam', { url })
  },
  refreshToken() {
    return axios.post('/v1/auth/refresh')
  },
  getAccountDetails() {
    return axios.get('/v1/auth/account')
  },
  editAccount(payload) {
    return axios.patch('/v1/auth/account', payload)
  },
  performDevLogin(nickname, steamId = null) {
    return axios.post('/v1/auth/dev-login', { nickname, steam_id: steamId })
  }
}

export default v1
