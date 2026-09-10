import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const request = axios.create({
  baseURL: '/api',
  timeout: 90000
})

request.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  res => {
    const body = res.data
    if (body.code === 0) return body.data
    ElMessage.error(body.message || '请求失败')
    return Promise.reject(new Error(body.message || '请求失败'))
  },
  err => {
    const status = err.response?.status
    const message = err.response?.data?.message
    if (status === 401 && router.currentRoute.value.path !== '/login') {
      localStorage.removeItem('access_token')
      if (!message || !message.includes('无效')) {
        ElMessage.error('登录已过期，请重新登录')
      }
      router.push('/login')
    } else if (message) {
      ElMessage.error(message)
    } else {
      ElMessage.error('网络异常，请稍后重试')
    }
    return Promise.reject(err)
  }
)

export default request
