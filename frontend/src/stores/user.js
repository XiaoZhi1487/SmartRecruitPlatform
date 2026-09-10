import { defineStore } from 'pinia'
import { authApi } from '../api'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    profile: null,
    token: localStorage.getItem('access_token') || ''
  }),
  getters: {
    isLoggedIn: s => !!s.token,
    isAdmin: s => s.user?.role === 'admin',
    isEnterprise: s => ['enterprise', 'admin'].includes(s.user?.role)
  },
  actions: {
    setToken(token) {
      this.token = token
      localStorage.setItem('access_token', token)
    },
    async login(account, password) {
      const data = await authApi.login(account, password)
      this.setToken(data.tokens.access_token)
      this.user = data.user
      return data
    },
    async fetchMe() {
      const data = await authApi.me()
      this.user = data.user
      this.profile = data.profile
    },
    setProfile(profile) {
      this.profile = profile
    },
    logout() {
      this.token = ''
      this.user = null
      this.profile = null
      localStorage.removeItem('access_token')
    }
  }
})
