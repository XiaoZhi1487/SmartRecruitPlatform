import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/Login.vue'), meta: { title: '登录' } },
  { path: '/register', name: 'register', component: () => import('../views/Register.vue'), meta: { title: '注册' } },
  {
    path: '/',
    component: () => import('../components/AppLayout.vue'),
    redirect: '/home',
    children: [
      { path: 'home', name: 'home', component: () => import('../views/Home.vue'), meta: { title: '职位大厅' } },
      { path: 'analysis', name: 'analysis', component: () => import('../views/Analysis.vue'), meta: { title: '市场分析' } },
      { path: 'favorites', name: 'favorites', component: () => import('../views/Favorites.vue'), meta: { title: '我的收藏', auth: true } },
      { path: 'job/:id', name: 'jobDetail', component: () => import('../views/JobDetail.vue'), meta: { title: '职位详情' } },
      { path: 'recommend', name: 'recommend', component: () => import('../views/Recommend.vue'), meta: { title: '智能推荐', auth: true } },
      { path: 'chat', name: 'chat', component: () => import('../views/AIChat.vue'), meta: { title: 'AI职业助手', auth: true } },
      { path: 'crawler', name: 'crawler', component: () => import('../views/Crawler.vue'), meta: { title: '爬虫控制台', auth: true } },
      { path: 'resume', name: 'resume', component: () => import('../views/Resume.vue'), meta: { title: '我的简历', auth: true } },
      { path: 'profile', name: 'profile', component: () => import('../views/Profile.vue'), meta: { title: '个人中心', auth: true } },
      { path: 'admin', name: 'admin', component: () => import('../views/Admin.vue'), meta: { title: '管理后台', auth: true, admin: true } }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/home' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(to => {
  document.title = `${to.meta.title || ''} - 智聘通`
  const store = useUserStore()
  if (to.meta.admin && !store.isAdmin) return '/home'
  if (to.meta.auth && !store.isLoggedIn) return '/login'
  if ((to.name === 'login' || to.name === 'register') && store.isLoggedIn) return '/home'
})

export default router
