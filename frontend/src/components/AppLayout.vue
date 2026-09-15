<template>
  <div class="layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: collapsed }">
      <div class="logo">
        <img src="/logo.png" class="logo-img" alt="智聘通" />
        <span v-if="!collapsed" class="logo-text">智聘通</span>
      </div>

      <nav class="menu">
        <router-link v-for="item in menus" :key="item.path" :to="item.path"
                     class="menu-item" :class="{ active: isActive(item) }"
                     :title="item.label">
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
          <span v-if="!collapsed" class="menu-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <el-button class="collapse-btn" text @click="collapsed = !collapsed">
          <el-icon><component :is="collapsed ? 'Expand' : 'Fold'" /></el-icon>
        </el-button>
      </div>
    </aside>

    <!-- 主区域 -->
    <div class="main">
      <header class="topbar">
        <div class="topbar-left">
          <span class="crumb">{{ route.meta.title || '智聘通' }}</span>
        </div>
        <div class="topbar-right">
          <template v-if="store.isLoggedIn">
            <el-dropdown @command="handleCommand">
              <span class="user-chip">
                <el-avatar :size="30" class="user-avatar">{{ avatarText }}</el-avatar>
                <span class="user-name">{{ store.user?.username }}</span>
                <el-tag v-if="store.isAdmin" size="small" type="danger" effect="dark">管理员</el-tag>
                <el-tag v-else-if="store.isEnterprise" size="small" type="warning">企业</el-tag>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile"><el-icon><User /></el-icon>个人中心</el-dropdown-item>
                  <el-dropdown-item command="resume"><el-icon><Document /></el-icon>我的简历</el-dropdown-item>
                  <el-dropdown-item command="logout" divided><el-icon><SwitchButton /></el-icon>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <el-button @click="$router.push('/login')">登录</el-button>
            <el-button type="primary" class="zp-btn-gradient" @click="$router.push('/register')">注册</el-button>
          </template>
        </div>
      </header>

      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const collapsed = ref(false)

const menus = computed(() => {
  const base = [
    { path: '/home', label: '职位大厅', icon: 'HomeFilled' },
    { path: '/analysis', label: '市场分析', icon: 'TrendCharts' },
    { path: '/favorites', label: '我的收藏', icon: 'Star' },
    { path: '/recommend', label: '智能推荐', icon: 'DataAnalysis' },
    { path: '/chat', label: 'AI职业助手', icon: 'ChatDotRound' },
    { path: '/crawler', label: '爬虫控制台', icon: 'Monitor' },
    { path: '/resume', label: '我的简历', icon: 'Document' },
    { path: '/profile', label: '个人中心', icon: 'User' }
  ]
  if (store.isAdmin) {
    base.push({ path: '/admin', label: '管理后台', icon: 'Setting' })
  }
  return base
})

const avatarText = computed(() => (store.user?.username || '?').slice(0, 1).toUpperCase())

function isActive(item) {
  if (item.path === '/home') return route.path === '/home'
  return route.path.startsWith(item.path)
}

function handleCommand(cmd) {
  if (cmd === 'logout') {
    store.logout()
    router.push('/login')
  } else {
    router.push(`/${cmd}`)
  }
}
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: #0f172a;
  color: #cbd5e1;
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease;
}
.sidebar.collapsed {
  width: 68px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 16px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.15);
}
.logo-img {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  border-radius: 10px;
  object-fit: cover;
}
.logo-text {
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 2px;
  white-space: nowrap;
}

.menu {
  flex: 1;
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border-radius: 10px;
  color: #94a3b8;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}
.menu-item:hover {
  background: rgba(148, 163, 184, 0.12);
  color: #e2e8f0;
}
.menu-item.active {
  background: var(--zp-gradient);
  color: #fff;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
}

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid rgba(148, 163, 184, 0.15);
}
.collapse-btn {
  color: #94a3b8;
  width: 100%;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid var(--zp-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}
.crumb {
  font-size: 16px;
  font-weight: 600;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
}
.user-chip:hover {
  background: #f1f5f9;
}
.user-avatar {
  background: var(--zp-gradient);
  color: #fff;
  font-weight: 600;
}
.user-name {
  font-size: 14px;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 4px;
}
</style>
