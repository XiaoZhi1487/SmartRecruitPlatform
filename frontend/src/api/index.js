import request from './request'

// ============ 认证 ============
export const authApi = {
  register: data => request.post('/auth/register', data),
  login: (account, password) => request.post('/auth/login', { account, password }),
  me: () => request.get('/auth/me'),
  refresh: () => request.post('/auth/refresh'),
  verifyEmail: token => request.get('/auth/verify-email', { params: { token } }),
  forgotPassword: email => request.post('/auth/forgot-password', { email }),
  resetPassword: data => request.post('/auth/reset-password', data)
}

// ============ 用户资料 ============
export const userApi = {
  getProfile: () => request.get('/user/profile'),
  updateProfile: data => request.put('/user/profile', data),
  addEducation: data => request.post('/user/profile/educations', data),
  updateEducation: (id, data) => request.put(`/user/profile/educations/${id}`, data),
  deleteEducation: id => request.delete(`/user/profile/educations/${id}`),
  addWork: data => request.post('/user/profile/works', data),
  updateWork: (id, data) => request.put(`/user/profile/works/${id}`, data),
  deleteWork: id => request.delete(`/user/profile/works/${id}`),
  addSkill: data => request.post('/user/profile/skills', data),
  updateSkill: (id, data) => request.put(`/user/profile/skills/${id}`, data),
  deleteSkill: id => request.delete(`/user/profile/skills/${id}`),
  changePassword: data => request.post('/user/change-password', data)
}

// ============ 职位 ============
export const jobApi = {
  list: params => request.get('/jobs', { params }),
  cities: () => request.get('/jobs/cities'),
  stats: () => request.get('/jobs/stats'),
  analysis: () => request.get('/jobs/analysis'),
  detail: id => request.get(`/jobs/${id}`),
  favorite: id => request.post(`/jobs/${id}/favorite`),
  unfavorite: id => request.delete(`/jobs/${id}/favorite`),
  favorites: () => request.get('/jobs/favorites/list'),
  redirect: id => request.get(`/jobs/${id}/redirect`),
  analyze: id => request.post(`/jobs/${id}/analyze`)
}

// ============ 简历 ============
export const resumeApi = {
  upload: formData => request.post('/resume/upload', formData),
  list: () => request.get('/resume'),
  detail: id => request.get(`/resume/${id}`),
  remove: id => request.delete(`/resume/${id}`),
  optimize: (id, data) => request.post(`/resume/${id}/optimize`, data)
}

// ============ 爬虫 ============
export const crawlApi = {
  start: data => request.post('/crawl/start', data),
  stop: () => request.post('/crawl/stop'),
  status: () => request.get('/crawl/status'),
  logs: params => request.get('/crawl/logs', { params }),
  tasks: params => request.get('/crawl/tasks', { params }),
  structureCheck: () => request.post('/crawl/structure-check'),
  structureChecks: () => request.get('/crawl/structure-checks'),
  clear: () => request.post('/crawl/clear')
}

// ============ AI对话 ============
export const chatApi = {
  createSession: data => request.post('/chat/sessions', data),
  listSessions: () => request.get('/chat/sessions'),
  messages: id => request.get(`/chat/sessions/${id}/messages`),
  send: (id, content) => request.post(`/chat/sessions/${id}/messages`, { content }),
  deleteSession: id => request.delete(`/chat/sessions/${id}`)
}

// ============ 智能推荐 ============
export const recommendApi = {
  jobs: params => request.get('/recommend/jobs', { params }),
  candidates: params => request.get('/recommend/candidates', { params }),
  overview: () => request.get('/recommend/overview'),
  feedback: data => request.post('/recommend/feedback', data)
}

// ============ 管理后台 ============
export const adminApi = {
  stats: () => request.get('/admin/stats'),
  users: params => request.get('/admin/users', { params }),
  updateUser: (id, data) => request.patch(`/admin/users/${id}`, data),
  createUser: data => request.post('/admin/users', data),
  deleteJob: id => request.delete(`/admin/jobs/${id}`),
  cleanupJobs: data => request.post('/admin/jobs/cleanup', data),
  crawlTasks: params => request.get('/admin/crawl-tasks', { params })
}
