<template>
  <div class="zp-page">
    <h2 class="zp-page-title"><el-icon><Document /></el-icon> 我的简历</h2>
    <p class="zp-page-sub">支持 PDF / Word / TXT 上传解析，自动提取关键信息，AI 优化建议</p>

    <!-- 上传区 -->
    <el-upload drag :auto-upload="false" :show-file-list="false" :on-change="onFileChange"
               accept=".pdf,.doc,.docx,.txt" class="upload-area">
      <el-icon class="upload-icon"><UploadFilled /></el-icon>
      <div class="upload-text">拖拽简历文件到此处，或 <em>点击上传</em></div>
      <template #tip>
        <div class="upload-tip">支持 PDF / Word / TXT，文件不超过 16MB</div>
      </template>
    </el-upload>

    <!-- 简历列表 -->
    <div class="resume-list" v-loading="loading">
      <div v-for="r in resumes" :key="r.id" class="resume-card zp-card">
        <div class="rc-icon" :class="'type-' + r.file_type">
          <el-icon><Document /></el-icon>
        </div>
        <div class="rc-info">
          <div class="rc-name">{{ r.file_name }}</div>
          <div class="rc-meta">
            {{ r.file_type.toUpperCase() }} · {{ (r.file_size / 1024).toFixed(1) }}KB ·
            {{ fmtTime(r.created_at) }}
            <el-tag :type="r.parse_status === 'success' ? 'success' : r.parse_status === 'failed' ? 'danger' : 'warning'"
                    size="small" class="status-tag">{{ statusText[r.parse_status] }}</el-tag>
          </div>
        </div>
        <div class="rc-actions">
          <el-button size="small" @click="viewDetail(r)">查看解析</el-button>
          <el-button size="small" type="primary" class="zp-btn-gradient"
                     :disabled="r.parse_status !== 'success'" @click="openOptimize(r)">AI优化</el-button>
          <el-button size="small" type="danger" text @click="removeResume(r)">删除</el-button>
        </div>
      </div>
      <el-empty v-if="!loading && !resumes.length" description="还没有简历，上传一份开始吧" />
    </div>

    <!-- 解析详情抽屉 -->
    <el-drawer v-model="detailVisible" :title="current?.file_name || '简历解析'" size="46%">
      <template v-if="currentDetail">
        <h4 class="drawer-title">结构化信息</h4>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="姓名">{{ sd.real_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="电话">{{ sd.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ sd.email || '-' }}</el-descriptions-item>
          <el-descriptions-item label="学历">{{ sd.education_level || '-' }}</el-descriptions-item>
          <el-descriptions-item label="工作年限">{{ sd.experience_years ?? '-' }} 年</el-descriptions-item>
          <el-descriptions-item label="期望岗位">{{ sd.expected_position || '-' }}</el-descriptions-item>
        </el-descriptions>
        <h4 class="drawer-title">技能</h4>
        <div class="skill-tags">
          <el-tag v-for="s in (sd.skills || [])" :key="s.name" size="small" effect="plain">{{ s.name }}</el-tag>
          <span v-if="!(sd.skills || []).length" class="muted">未识别</span>
        </div>
        <h4 class="drawer-title">教育经历</h4>
        <div v-for="(e, i) in (sd.educations || [])" :key="i" class="edu-item">
          {{ e.school }} · {{ e.major || '-' }} · {{ e.degree || '-' }} ({{ e.start_date }} ~ {{ e.end_date }})
        </div>
        <h4 class="drawer-title">工作经历</h4>
        <div v-for="(w, i) in (sd.works || [])" :key="i" class="edu-item">
          {{ w.company }} · {{ w.position }} ({{ w.start_date }} ~ {{ w.end_date }})
          <div class="muted">{{ w.description }}</div>
        </div>
        <h4 class="drawer-title">原文预览</h4>
        <div class="raw-text">{{ currentDetail.raw_text }}</div>
      </template>
      <el-empty v-else description="暂无解析数据" />
    </el-drawer>

    <!-- AI优化弹窗 -->
    <el-dialog v-model="optimizeVisible" title="AI 简历优化建议" width="640px">
      <div class="opt-form">
        <el-input v-model="optJobTitle" placeholder="输入目标岗位，如：Python后端工程师" clearable>
          <template #prefix><el-icon><Briefcase /></el-icon></template>
        </el-input>
        <el-button type="primary" class="zp-btn-gradient" :loading="optimizing" @click="runOptimize">
          生成优化建议
        </el-button>
      </div>
      <div v-if="optResult" class="opt-result">
        <div class="opt-score">
          简历评分 <b class="score">{{ optResult.score ?? '-' }}</b> / 100
        </div>
        <div class="opt-overall">{{ optResult.overall }}</div>
        <div v-for="s in (optResult.suggestions || [])" :key="s.dimension" class="opt-item">
          <div class="opt-dim">{{ s.dimension }}</div>
          <div class="opt-advice">{{ s.advice }}</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { resumeApi } from '../api'

const resumes = ref([])
const loading = ref(false)
const current = ref(null)
const currentDetail = ref(null)
const detailVisible = ref(false)
const optimizeVisible = ref(false)
const optJobTitle = ref('')
const optResult = ref(null)
const optimizing = ref(false)

const statusText = { pending: '解析中', success: '解析成功', failed: '解析失败' }

onMounted(load)

async function load() {
  loading.value = true
  try {
    resumes.value = await resumeApi.list()
  } finally {
    loading.value = false
  }
}

async function onFileChange(file) {
  if (file.size > 16 * 1024 * 1024) {
    ElMessage.error('文件超过 16MB 限制')
    return
  }
  const fd = new FormData()
  fd.append('file', file.raw)
  await resumeApi.upload(fd)
  ElMessage.success('上传成功，正在解析...')
  load()
  // 轮询刷新解析状态
  const timer = setInterval(async () => {
    const list = await resumeApi.list()
    resumes.value = list
    const target = list.find(r => r.file_name === file.name)
    if (!target || target.parse_status !== 'pending') {
      clearInterval(timer)
    }
  }, 1500)
}

async function viewDetail(r) {
  current.value = r
  currentDetail.value = await resumeApi.detail(r.id)
  detailVisible.value = true
}

const sd = computed(() => currentDetail.value?.structured || {})

function openOptimize(r) {
  current.value = r
  optJobTitle.value = ''
  optResult.value = null
  optimizeVisible.value = true
}

async function runOptimize() {
  optimizing.value = true
  try {
    optResult.value = await resumeApi.optimize(current.value.id, { job_title: optJobTitle.value })
  } finally {
    optimizing.value = false
  }
}

async function removeResume(r) {
  await ElMessageBox.confirm(`确定删除简历「${r.file_name}」？`, '提示', { type: 'warning' })
  await resumeApi.remove(r.id)
  ElMessage.success('已删除')
  load()
}

function fmtTime(s) {
  return s ? new Date(s).toLocaleString('zh-CN', { hour12: false }) : '-'
}
</script>

<style scoped>
.upload-area {
  margin-bottom: 18px;
}
.upload-icon {
  font-size: 46px;
  color: var(--zp-primary-light);
}
.upload-text {
  color: var(--zp-text-secondary);
  font-size: 14px;
}
.upload-text em {
  color: var(--zp-primary);
  font-style: normal;
}
.upload-tip {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}
.resume-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 120px;
}
.resume-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
}
.rc-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}
.type-pdf { background: #fee2e2; color: #dc2626; }
.type-docx, .type-doc { background: #dbeafe; color: #2563eb; }
.type-txt { background: #dcfce7; color: #16a34a; }
.rc-info {
  flex: 1;
  min-width: 0;
}
.rc-name {
  font-weight: 600;
  font-size: 15px;
}
.rc-meta {
  font-size: 12px;
  color: var(--zp-text-secondary);
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.rc-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.drawer-title {
  margin: 18px 0 10px;
  font-size: 15px;
}
.skill-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.edu-item {
  padding: 6px 0;
  font-size: 14px;
  color: #334155;
}
.muted {
  color: #94a3b8;
  font-size: 13px;
}
.raw-text {
  background: #f8fafc;
  border: 1px solid var(--zp-border);
  border-radius: 8px;
  padding: 12px;
  font-size: 13px;
  line-height: 1.8;
  max-height: 260px;
  overflow-y: auto;
  white-space: pre-wrap;
}
.opt-form {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.opt-result {
  border-top: 1px solid var(--zp-border);
  padding-top: 16px;
}
.opt-score {
  font-size: 16px;
  margin-bottom: 10px;
}
.opt-score .score {
  color: var(--zp-primary);
  font-size: 24px;
}
.opt-overall {
  background: #f5f3ff;
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 14px;
  color: #334155;
  line-height: 1.8;
}
.opt-item {
  border: 1px solid var(--zp-border);
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 10px;
}
.opt-dim {
  font-weight: 700;
  color: var(--zp-primary);
  font-size: 13px;
  margin-bottom: 6px;
}
.opt-advice {
  font-size: 14px;
  line-height: 1.8;
  color: #334155;
}
</style>
