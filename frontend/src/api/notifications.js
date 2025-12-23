import axios from 'axios'

export const v1 = {
  getNotifications(limit = 10, offset = 0, includeSeen = false) {
    return axios.get(`/v1/notifications?limit=${limit}&offset=${offset}&includeSeen=${includeSeen}`)
  },
  getUnseenNotificationCount() {
    return axios.get('/v1/notifications/unseen')
  },
  markAllNotificationsRead() {
    return axios.patch('/v1/notifications/read-all')
  }
}

export default v1
