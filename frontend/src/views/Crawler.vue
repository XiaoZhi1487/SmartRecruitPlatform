<template>
  <div class="page">
    <h2 class="zp-page-title"><el-icon><Monitor /></el-icon> 爬虫控制台</h2>
    <p class="zp-page-sub">Selenium 多线程爬取 Boss直聘 职位 · 反爬策略 · 结构变更监测</p>

    <!-- 任务表单 -->
    <section class="crawl-form zp-card">
      <div class="form-grid">
        <div class="form-item full">
          <label>爬取关键字（逗号分隔，支持多关键字并发）</label>
          <el-input v-model="form.keywords" placeholder="如：Python, Java, 数据分析, 前端" />
        </div>
        <div class="form-item">
          <label>城市代码（留空为全国）</label>
          <el-input v-model="form.city" placeholder="如：101010100(北京)" />
        </div>
        <div class="form-item">
          <label>爬取页数（每页10条）</label>
          <el-input-number v-model="form.pages" :min="1" :max="20" />
        </div>
        <div class="form-item">
          <label>并发线程数</label>
          <el-input-number v-model="form.threads" :min="1" :max="8" />
        </div>
        <div class="form-item">
          <label>爬取模式</label>
          <el-radio-group v-model="form.mode">
            <el-radio-button label="auto">自动</el-radio-button>
            <el-radio-button label="real">真实</el-radio-button>
            <el-radio-button label="mock">模拟</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <div class="form-actions">
        <el-button type="primary" class="zp-btn-gradient" :disabled="running"
                   :loading="starting" @click="startCrawl">
          <el-icon><VideoPlay /></el-icon> 启动爬取
        </el-button>
        <el-button type="danger" plain :disabled="!running" @click="stopCrawl">
          <el-icon><VideoPause /></el-icon> 停止
        </el-button>
        <el-button :disabled="running" @click="runStructureCheck">
          <el-icon><Odometer /></el-icon> 结构变更监测
        </el-button>
      </div>
    </section>

    <!-- 运行状态 -->
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

    <!-- 结构监测结果 -->
    <section class="check-panel zp-card" v-if="checks.length">
      <div class="panel-title"><el-icon><Odometer /></el-icon> 网站结构监测记录</div>
      <el-table :data="checks" size="small" max-height="220">
        <el-table-column prop="created_at" label="检测时间" width="170">
          <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="selector_key" label="选择器" width="140" />
        <el-table-column prop="selector" label="表达式" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'ok' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="evidence" label="证据" show-overflow-tooltip />
      </el-table>
    </section>

    <!-- 运行日志 -->
    <section class="log-panel zp-card">
      <div class="panel-title"><el-icon><Document /></el-icon> 运行日志</div>
      <el-table :data="logs" size="small" max-height="360">
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="level" label="级别" width="80">
          <template #default="{ row }">
            <el-tag :type="row.level === 'error' ? 'danger' : row.level === 'warn' ? 'warning' : 'info'"
                    size="small">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="keyword" label="关键字" width="110" />
        <el-table-column prop="page" label="页" width="60" />
        <el-table-column prop="message" label="内容" show-overflow-tooltip />
      </el-table>
    </section>

    <!-- 任务历史 -->
    <section class="task-panel zp-card">
      <div class="panel-title"><el-icon><Clock /></el-icon> 任务历史</div>
      <el-table :data="tasks" size="small" max-height="300">
        <el-table-column prop="keywords" label="关键字" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'done' ? 'success' : row.status === 'running' ? 'primary' : 'info'"
                    size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="mode" label="模式" width="140" />
        <el-table-column prop="total_found" label="找到" width="80" />
        <el-table-column prop="total_saved" label="保存" width="80" />
        <el-table-column prop="captcha_hits" label="验证码" width="80" />
        <el-table-column prop="message" label="信息" show-overflow-tooltip />
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { crawlApi } from '../api'

const form = reactive({ keywords: 'Python, Java, 数据分析', city: '', pages: 3, threads: 3, mode: 'auto' })
const starting = ref(false)
const running = ref(false)
const stats = reactive({ found: 0, saved: 0, captcha: 0, queue_size: 0 })
const logs = ref([])
const tasks = ref([])
const checks = ref([])
let timer = null

const statCards = computed(() => [
  { label: '已发现职位', value: stats.found, icon: 'Search', bg: '#eef2ff', color: '#4f46e5' },
  { label: '已保存职位', value: stats.saved, icon: 'CircleCheck', bg: '#ecfdf5', color: '#059669' },
  { label: '验证码命中', value: stats.captcha, icon: 'Warning', bg: '#fef3c7', color: '#d97706' },
  { label: '任务队列', value: stats.queue_size, icon: 'List', bg: '#fdf2f8', color: '#db2777' }
])

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 3000)
})

onBeforeUnmount(() => timer && clearInterval(timer))

async function refresh() {
  try {
    const st = await crawlApi.status()
    running.value = st.running
    Object.assign(stats, st.stats)
    stats.queue_size = st.queue_size
    if (st.running || !logs.value.length) {
      const lg = await crawlApi.logs({ page: 1, page_size: 20 })
      logs.value = lg.items
    }
    const tk = await crawlApi.tasks({ page: 1, page_size: 8 })
    tasks.value = tk.items
    if (!checks.value.length) {
      const ch = await crawlApi.structureChecks()
      checks.value = ch || []
    }
  } catch (e) { /* ignore */ }
}

async function startCrawl() {
  if (!form.keywords.trim()) {
    ElMessage.warning('请填写关键字')
    return
  }
  starting.value = true
  try {
    await crawlApi.start(form)
    ElMessage.success('爬取任务已启动')
    refresh()
  } finally {
    starting.value = false
  }
}

async function stopCrawl() {
  await crawlApi.stop()
  ElMessage.info('已发送停止指令')
  setTimeout(refresh, 1500)
}

async function runStructureCheck() {
  await crawlApi.structureCheck()
  ElMessage.success('结构监测已触发，请在监测记录中查看')
  setTimeout(async () => {
    checks.value = await crawlApi.structureChecks()
  }, 3000)
}

function fmtTime(s) {
  return s ? new Date(s).toLocaleString('zh-CN', { hour12: false }) : '-'
}
</script>

<style scoped>
.crawl-form {
  padding: 22px;
  margin-bottom: 16px;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 18px;
}
.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-item.full {
  grid-column: 1 / -1;
}
.form-item label {
  font-size: 13px;
  color: var(--zp-text-secondary);
}
.form-actions {
  display: flex;
  gap: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
}
.stat-icon {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}
.stat-num {
  font-size: 22px;
  font-weight: 800;
}
.stat-label {
  font-size: 13px;
  color: var(--zp-text-secondary);
}

.check-panel, .log-panel, .task-panel {
  padding: 18px 20px;
  margin-bottom: 16px;
}
.panel-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
