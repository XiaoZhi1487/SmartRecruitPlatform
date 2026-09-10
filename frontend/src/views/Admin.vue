<template>
  <div class="page">
    <h2 class="zp-page-title"><el-icon><Setting /></el-icon> 管理后台</h2>
    <p class="zp-page-sub">系统统计 · 用户管理 · 数据管理 · 爬取任务监控</p>

    <!-- 系统统计 -->
    <section class="stats-grid">
      <div class="stat-card zp-card" v-for="s in statCards" :key="s.label">
        <div class="stat-icon" :style="{ background: s.bg, color: s.color }">
          <el-icon><component :is="s.icon" /></el-icon>
        </div>
        <div>
          <div class="stat-num">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>
    </section>

    <!-- 用户管理 -->
    <section class="panel zp-card">
      <div class="panel-head">
        <div class="panel-title"><el-icon><User /></el-icon> 用户管理</div>
        <div class="panel-actions">
          <el-input v-model="userKw" placeholder="搜索用户名 / 邮箱" clearable style="width: 220px"
                    @keyup.enter="loadUsers" @clear="loadUsers" />
          <el-button type="primary" class="zp-btn-gradient" @click="openCreate">
            <el-icon><Plus /></el-icon> 新增用户
          </el-button>
        </div>
      </div>
      <el-table :data="users" size="small" v-loading="userLoading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="130" />
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
        <el-table-column prop="role" label="角色" width="110">
          <template #default="{ row }">
            <el-select :model-value="row.role" size="small" style="width: 100px"
                       @change="v => changeRole(row, v)">
              <el-option label="求职者" value="user" />
              <el-option label="企业" value="enterprise" />
              <el-option label="管理员" value="admin" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="email_verified" label="邮箱验证" width="90">
          <template #default="{ row }">
            <el-tag :type="row.email_verified ? 'success' : 'info'" size="small">
              {{ row.email_verified ? '已验证' : '未验证' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="90">
          <template #default="{ row }">
            <el-switch :model-value="row.is_active" size="small"
                       @change="v => toggleActive(row, v)" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="160">
          <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="last_login_at" label="最近登录" width="160">
          <template #default="{ row }">{{ fmtTime(row.last_login_at) }}</template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination layout="total, prev, pager, next" :total="userTotal"
                       :page-size="userPageSize" :current-page="userPage"
                       @current-change="p => { userPage = p; loadUsers() }" />
      </div>
    </section>

    <!-- 数据管理 -->
    <section class="panel zp-card">
      <div class="panel-head">
        <div class="panel-title"><el-icon><DataBoard /></el-icon> 数据管理</div>
      </div>
      <div class="data-ops">
        <el-input v-model="cleanupSource" placeholder="按来源清理，如 boss（留空清理全部）" style="width: 260px" />
        <el-button type="danger" plain :loading="cleaning" @click="cleanupJobs">
          <el-icon><Delete /></el-icon> 清理职位数据
        </el-button>
      </div>
    </section>

    <!-- 爬取任务 -->
    <section class="panel zp-card">
      <div class="panel-head">
        <div class="panel-title"><el-icon><Odometer /></el-icon> 爬取任务</div>
        <el-button size="small" @click="loadTasks"><el-icon><Refresh /></el-icon> 刷新</el-button>
      </div>
      <el-table :data="tasks" size="small" max-height="360">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="keywords" label="关键字" width="170" />
        <el-table-column prop="mode" label="模式" width="90" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'done' ? 'success' : row.status === 'running' ? 'primary' : 'info'"
                    size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_found" label="找到" width="70" />
        <el-table-column prop="total_saved" label="保存" width="70" />
        <el-table-column prop="captcha_hits" label="验证码" width="70" />
        <el-table-column prop="created_at" label="开始时间" width="160">
          <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="message" label="信息" show-overflow-tooltip />
      </el-table>
    </section>

    <!-- 新增用户对话框 -->
    <el-dialog v-model="createVisible" title="新增用户" width="420px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="用户名"><el-input v-model="createForm.username" placeholder="3-20位字母数字下划线" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="createForm.email" placeholder="user@example.com" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="createForm.password" type="password" show-password placeholder="至少8位，含大小写字母与数字" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="createForm.role" style="width: 100%">
            <el-option label="求职者" value="user" />
            <el-option label="企业" value="enterprise" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" class="zp-btn-gradient" :loading="creating" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi } from '../api'

const statCards = ref([])
const users = ref([])
const userPage = ref(1)
const userPageSize = 10
const userTotal = ref(0)
const userKw = ref('')
const userLoading = ref(false)

const tasks = ref([])
const cleanupSource = ref('')
const cleaning = ref(false)

const createVisible = ref(false)
const creating = ref(false)
const createForm = reactive({ username: '', email: '', password: '', role: 'user' })

onMounted(() => {
  loadStats()
  loadUsers()
  loadTasks()
})

async function loadStats() {
  try {
    const s = await adminApi.stats()
    statCards.value = [
      { label: '用户总数', value: s.users, icon: 'User', bg: '#eef2ff', color: '#4f46e5' },
      { label: '职位总数', value: s.jobs, icon: 'Briefcase', bg: '#ecfdf5', color: '#059669' },
      { label: '在招职位', value: s.active_jobs, icon: 'CircleCheck', bg: '#eff6ff', color: '#2563eb' },
      { label: '公司数量', value: s.companies, icon: 'OfficeBuilding', bg: '#fef3c7', color: '#d97706' },
      { label: '简历数量', value: s.resumes, icon: 'Document', bg: '#fdf2f8', color: '#db2777' },
      { label: 'AI会话', value: s.chat_sessions, icon: 'ChatDotRound', bg: '#f0fdf4', color: '#16a34a' },
      { label: '爬取任务', value: s.crawl_tasks, icon: 'Odometer', bg: '#f5f3ff', color: '#7c3aed' }
    ]
  } catch (e) { /* ignore */ }
}

async function loadUsers() {
  userLoading.value = true
  try {
    const res = await adminApi.users({ page: userPage.value, page_size: userPageSize, keyword: userKw.value })
    users.value = res.items
    userTotal.value = res.total
  } finally {
    userLoading.value = false
  }
}

async function changeRole(row, role) {
  await adminApi.updateUser(row.id, { role })
  row.role = role
  ElMessage.success('角色已更新')
}

async function toggleActive(row, val) {
  await adminApi.updateUser(row.id, { is_active: val })
  row.is_active = val
  ElMessage.success(val ? '用户已启用' : '用户已禁用')
}

function openCreate() {
  Object.assign(createForm, { username: '', email: '', password: '', role: 'user' })
  createVisible.value = true
}

async function submitCreate() {
  if (!createForm.username || !createForm.email || !createForm.password) {
    ElMessage.warning('请完整填写表单')
    return
  }
  creating.value = true
  try {
    await adminApi.createUser({ ...createForm })
    ElMessage.success('用户创建成功')
    createVisible.value = false
    loadUsers()
    loadStats()
  } finally {
    creating.value = false
  }
}

async function cleanupJobs() {
  const source = cleanupSource.value.trim()
  const tip = source ? `按来源「${source}」` : '全部'
  try {
    await ElMessageBox.confirm(`确认${tip}清理职位数据？该操作不可恢复。`, '危险操作', { type: 'warning' })
  } catch (e) {
    return
  }
  cleaning.value = true
  try {
    const res = await adminApi.cleanupJobs({ source: source || undefined })
    ElMessage.success(`已清理 ${res.deleted} 条职位`)
    loadStats()
  } finally {
    cleaning.value = false
  }
}

async function loadTasks() {
  try {
    const res = await adminApi.crawlTasks({ page: 1, page_size: 10 })
    tasks.value = res.items
  } catch (e) { /* ignore */ }
}

function fmtTime(s) {
  return s ? new Date(s).toLocaleString('zh-CN', { hour12: false }) : '-'
}
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px;
}
.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.stat-num {
  font-size: 20px;
  font-weight: 800;
  line-height: 1.2;
}
.stat-label {
  font-size: 12px;
  color: var(--zp-text-secondary);
}
.panel {
  padding: 18px 20px;
  margin-bottom: 16px;
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.panel-title {
  font-size: 15px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}
.panel-actions {
  display: flex;
  gap: 10px;
}
.pager {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}
.data-ops {
  display: flex;
  gap: 12px;
  align-items: center;
}
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
