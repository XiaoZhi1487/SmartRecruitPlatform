<template>
  <div class="page">
    <h2 class="zp-page-title"><el-icon><Monitor /></el-icon> 爬虫控制台</h2>
    <p class="zp-page-sub">Selenium 多线程爬取 前程无忧 职位 · 反爬策略 · 结构变更监测</p>

    <!-- 任务表单 -->
    <section class="crawl-form zp-card">
      <div class="form-grid">
        <div class="form-item full">
          <label>爬取关键字（逗号分隔，支持多关键字并发）</label>
          <el-input v-model="form.keywords" placeholder="如：Python, Java, 数据分析, 前端" />
        </div>
        <div class="form-item">
          <label>工作地点（必选，爬取该城市的职位）</label>
          <el-select v-model="form.city" filterable allow-create clearable
                     placeholder="请选择要爬取的城市" style="width: 100%">
            <el-option label="北京" value="010000" />
            <el-option label="上海" value="020000" />
            <el-option label="广州" value="030200" />
            <el-option label="深圳" value="040000" />
            <el-option label="杭州" value="080200" />
            <el-option label="南京" value="070200" />
            <el-option label="苏州" value="070300" />
            <el-option label="成都" value="090200" />
            <el-option label="武汉" value="180200" />
            <el-option label="西安" value="200200" />
            <el-option label="重庆" value="060000" />
            <el-option label="东莞" value="030800" />
            <el-option label="南宁" value="140200" />
            <el-option label="柳州" value="140400" />
            <el-option label="福州" value="110200" />
            <el-option label="济南" value="120200" />
            <el-option label="青岛" value="120300" />
            <el-option label="合肥" value="150200" />
            <el-option label="郑州" value="170200" />
            <el-option label="长沙" value="190200" />
            <el-option label="沈阳" value="230200" />
            <el-option label="昆明" value="250200" />
            <el-option label="贵阳" value="260200" />
          </el-select>
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
            <el-radio-button value="auto">自动</el-radio-button>
            <el-radio-button value="real">真实</el-radio-button>
            <el-radio-button value="mock">模拟</el-radio-button>
          </el-radio-group>
        </div>
        <div class="form-item">
          <label>浏览器窗口</label>
          <el-checkbox v-model="form.show_browser">显示浏览器（便于人工处理验证码）</el-checkbox>
        </div>
      </div>
      <el-alert v-if="form.mode === 'real' || form.mode === 'auto'" type="info" :closable="false"
                class="crawl-tip" show-icon>
        前程无忧无需登录即可爬取。请选择<b>具体城市</b>（如柳州、上海），将爬取该城市的前程无忧职位。
        命中验证码时会弹出浏览器窗口，请在窗口中完成验证后自动继续；真实爬取无产出时自动降级为模拟数据。
      </el-alert>
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
        <el-button type="danger" plain :disabled="running" :loading="clearing" @click="clearCrawlData">
          <el-icon><Delete /></el-icon> 清空爬取数据
        </el-button>
      </div>
    </section>

    <!-- 实时运行状态 -->
    <section class="run-banner zp-card" v-if="running || current">
      <div class="run-info">
        <el-tag :type="running ? 'primary' : 'success'" effect="dark" size="large">
          <el-icon v-if="running" class="is-loading"><Loading /></el-icon>
          {{ running ? '运行中' : '收尾中' }}
        </el-tag>
        <span class="run-elapsed">
          <el-icon><Timer /></el-icon> 已运行 {{ elapsedText }}
        </span>
        <span v-if="current" class="run-current">
          <el-icon class="is-loading"><Loading /></el-icon>
          正在处理：{{ current[0] }} · 第{{ current[1] }}页
        </span>
        <span class="run-mode">模式：{{ modeText }}</span>
      </div>
      <el-progress :percentage="progressPercent" :stroke-width="10" :show-text="false"
                   style="margin-top: 12px" />
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { crawlApi } from '../api'
import { fmtTime } from '../utils/date'

const form = reactive({ keywords: 'Python, Java, 数据分析', city: '', pages: 3, threads: 3, mode: 'auto', show_browser: true })
const starting = ref(false)
const running = ref(false)
const stats = reactive({ found: 0, saved: 0, captcha: 0, queue_size: 0 })
const logs = ref([])
const tasks = ref([])
const checks = ref([])
const current = ref(null)        // [关键字, 页码] 当前处理进度
const modeUsed = ref('')         // 实际使用模式
const startedAt = ref(0)         // 任务启动时间戳
const nowTick = ref(0)           // 每秒自增，驱动运行时长刷新
const clearing = ref(false)
let timer = null
let elapsedTimer = null
let wasRunning = false           // 上一次轮询时的运行状态（用于结束提示）

const totalPages = computed(() => {
  const kws = (form.keywords || '').split(/[,，]/).map(s => s.trim()).filter(Boolean)
  return kws.length * (form.pages || 1)
})

const progressPercent = computed(() => {
  if (!totalPages.value) return 0
  const done = stats.found > 0 ? Math.round((stats.found / 10 / totalPages.value) * 100) : 0
  return Math.min(100, Math.max(done, stats.queue_size < 10 && running.value ? 5 : 0))
})

const elapsedText = computed(() => {
  if (!startedAt.value) return '-'
  void nowTick.value
  const s = Math.floor((Date.now() - startedAt.value) / 1000)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  const pad = n => String(n).padStart(2, '0')
  return h > 0 ? `${h}:${pad(m)}:${pad(sec)}` : `${pad(m)}:${pad(sec)}`
})

const modeText = computed(() => {
  const m = modeUsed.value || form.mode
  return ({ auto: '自动', real: '真实', mock: '模拟', 'auto(degraded)': '自动（已降级为模拟）' })[m] || m
})

const statCards = computed(() => [
  { label: '已发现职位', value: stats.found, icon: 'Search', bg: '#eef2ff', color: '#4f46e5' },
  { label: '已保存职位', value: stats.saved, icon: 'CircleCheck', bg: '#ecfdf5', color: '#059669' },
  { label: '验证码命中', value: stats.captcha, icon: 'Warning', bg: '#fef3c7', color: '#d97706' },
  { label: '任务队列', value: stats.queue_size, icon: 'List', bg: '#fdf2f8', color: '#db2777' }
])

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 2000)
  elapsedTimer = setInterval(() => nowTick.value++, 1000)
})

onBeforeUnmount(() => {
  timer && clearInterval(timer)
  elapsedTimer && clearInterval(elapsedTimer)
})

async function refresh() {
  try {
    const st = await crawlApi.status()
    const prevRunning = wasRunning
    running.value = st.running
    current.value = st.current || null
    modeUsed.value = st.mode_used || ''
    Object.assign(stats, st.stats)
    stats.queue_size = st.queue_size
    if (st.running && !startedAt.value) startedAt.value = Date.now()
    if (!st.running && startedAt.value) {
      startedAt.value = 0
      if (prevRunning) {
        ElMessage.success(`爬取任务已结束：共发现 ${st.stats.found} 条，保存 ${st.stats.saved} 条`)
      }
    }
    wasRunning = st.running
    // 运行中实时刷新日志；任务刚结束时强制刷新一次以展示最终日志
    if (st.running || !logs.value.length || (prevRunning && !st.running)) {
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
  if (!form.city) {
    ElMessage.warning('请选择要爬取的城市')
    return
  }
  starting.value = true
  try {
    await crawlApi.start({ ...form, headless: !form.show_browser })
    ElMessage.success('爬取任务已启动')
    startedAt.value = Date.now()
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

async function clearCrawlData() {
  try {
    await ElMessageBox.confirm(
      '将清空所有爬取产生的职位数据（真实爬取 + 模拟数据），种子演示数据保留。确定继续？',
      '清空爬取数据',
      { type: 'warning', confirmButtonText: '确认清空', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  clearing.value = true
  try {
    const res = await crawlApi.clear()
    ElMessage.success(`已清空 ${res?.deleted ?? 0} 条爬取数据`)
    refresh()
  } finally {
    clearing.value = false
  }
}

async function runStructureCheck() {
  await crawlApi.structureCheck()
  ElMessage.success('结构监测已触发，请在监测记录中查看')
  setTimeout(async () => {
    checks.value = await crawlApi.structureChecks()
  }, 3000)
}
</script>

<style scoped>
.crawl-form {
  padding: 22px;
  margin-bottom: 16px;
}
.run-banner {
  padding: 16px 20px;
  margin-bottom: 16px;
}
.run-info {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}
.run-elapsed, .run-current, .run-mode {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--zp-text-primary);
}
.run-current {
  color: var(--zp-primary, #4f46e5);
  font-weight: 600;
}
.run-mode {
  color: var(--zp-text-secondary);
  font-size: 13px;
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
