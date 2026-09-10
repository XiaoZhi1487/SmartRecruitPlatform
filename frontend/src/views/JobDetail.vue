<template>
  <div class="zp-page" v-loading="loading">
    <el-page-header @back="$router.back()" class="back-header">
      <template #content><span>职位详情</span></template>
    </el-page-header>

    <div v-if="job" class="detail-wrap">
      <!-- 头部 -->
      <section class="detail-head zp-card">
        <div class="head-main">
          <div>
            <h1 class="job-title">{{ job.title }}</h1>
            <div class="job-meta">
              <span><el-icon><LocationInformation /></el-icon>{{ job.city }}{{ job.district }}</span>
              <span v-if="job.experience_required"><el-icon><Briefcase /></el-icon>{{ job.experience_required }}</span>
              <span v-if="job.education_required"><el-icon><Reading /></el-icon>{{ job.education_required }}</span>
              <span><el-icon><OfficeBuilding /></el-icon>{{ job.company_name }}</span>
            </div>
            <div class="job-tags">
              <el-tag v-for="t in (job.job_tags || [])" :key="t" size="small" effect="plain" class="tag">{{ t }}</el-tag>
            </div>
          </div>
          <div class="head-side">
            <div class="salary">{{ job.salary_text }}</div>
            <div class="head-actions">
              <el-button :type="job.is_favorite ? 'danger' : 'primary'"
                         :class="{ 'zp-btn-gradient': !job.is_favorite }"
                         @click="toggleFavorite">
                <el-icon><StarFilled v-if="job.is_favorite" /><Star v-else /></el-icon>
                {{ job.is_favorite ? '已收藏' : '收藏职位' }}
              </el-button>
              <el-button type="success" class="jump-btn" @click="goSource">
                <el-icon><Position /></el-icon> 去Boss直聘查看
              </el-button>
            </div>
          </div>
        </div>
      </section>

      <!-- AI 分析 -->
      <section class="ai-card zp-card">
        <div class="ai-head">
          <div class="ai-badge"><el-icon><MagicStick /></el-icon> AI 岗位解读</div>
          <div class="ai-actions">
            <el-button v-if="!analysis" size="small" type="primary" class="zp-btn-gradient"
                       :loading="analyzing" @click="runAnalysis">生成深度解读</el-button>
            <el-button v-else size="small" text @click="analysis = null">收起</el-button>
          </div>
        </div>
        <div v-if="!analysis" class="ai-placeholder">
          <el-icon class="ph-icon"><MagicStick /></el-icon>
          <p>点击生成岗位核心技能、适配建议、成长路径与面试提示</p>
        </div>
        <div v-else class="ai-body">
          <div class="ai-item">
            <span class="ai-label">核心技能</span>
            <span class="ai-value">{{ (analysis.core_skills || []).join('、') }}</span>
          </div>
          <div class="ai-item">
            <span class="ai-label">适配建议</span>
            <span class="ai-value">{{ analysis.suitability_advice }}</span>
          </div>
          <div class="ai-item">
            <span class="ai-label">成长路径</span>
            <span class="ai-value">{{ analysis.career_growth }}</span>
          </div>
          <div class="ai-item">
            <span class="ai-label">面试提示</span>
            <span class="ai-value">{{ analysis.interview_tips }}</span>
          </div>
        </div>
      </section>

      <!-- 职位描述 -->
      <section class="detail-body zp-card">
        <div class="body-title"><el-icon><Document /></el-icon> 职位描述</div>
        <div class="zp-desc">{{ job.description || '暂无详细描述' }}</div>
      </section>

      <!-- 任职要求 -->
      <section class="detail-body zp-card" v-if="job.requirement">
        <div class="body-title"><el-icon><Checked /></el-icon> 任职要求</div>
        <div class="zp-desc">{{ job.requirement }}</div>
      </section>

      <!-- 福利 -->
      <section class="detail-body zp-card" v-if="(job.welfare || []).length">
        <div class="body-title"><el-icon><Present /></el-icon> 公司福利</div>
        <div class="welfare-list">
          <el-tag v-for="w in job.welfare" :key="w" size="default" effect="light" class="welfare-tag">{{ w }}</el-tag>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { jobApi } from '../api'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const job = ref(null)
const loading = ref(false)
const analysis = ref(null)
const analyzing = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    job.value = await jobApi.detail(route.params.id)
    // 若有登录且未收藏，尝试AI分析（可选）
  } finally {
    loading.value = false
  }
})

async function toggleFavorite() {
  if (!store.isLoggedIn) {
    router.push('/login')
    return
  }
  if (job.value.is_favorite) {
    await jobApi.unfavorite(job.value.id)
    job.value.is_favorite = false
  } else {
    await jobApi.favorite(job.value.id)
    job.value.is_favorite = true
  }
}

async function goSource() {
  if (!job.value.link) {
    ElMessage.warning('该职位暂无原文链接')
    return
  }
  window.open(job.value.link, '_blank')
}

async function runAnalysis() {
  if (!store.isLoggedIn) {
    router.push('/login')
    return
  }
  analyzing.value = true
  try {
    analysis.value = await jobApi.analyze(job.value.id)
  } catch (e) { /* handled */ } finally {
    analyzing.value = false
  }
}
</script>

<style scoped>
.back-header {
  margin-bottom: 14px;
}
.detail-wrap {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.detail-head {
  padding: 24px;
}
.head-main {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}
.job-title {
  margin: 0 0 12px;
  font-size: 24px;
}
.job-meta {
  display: flex;
  gap: 16px;
  color: var(--zp-text-secondary);
  font-size: 14px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.job-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.job-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.tag {
  background: #eef2ff;
  color: var(--zp-primary);
  border: none;
}
.head-side {
  text-align: right;
}
.salary {
  color: #f59e0b;
  font-size: 26px;
  font-weight: 800;
}
.head-actions {
  margin-top: 14px;
  display: flex;
  gap: 10px;
}
.jump-btn {
  background: #059669 !important;
  border: none !important;
  color: #fff !important;
}

.ai-card {
  padding: 18px 24px;
  border: 1px solid #c7d2fe;
  background: linear-gradient(120deg, #f5f3ff, #eef2ff);
}
.ai-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.ai-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  color: var(--zp-primary);
}
.ai-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ai-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--zp-text-secondary);
  padding: 18px 0;
}
.ph-icon {
  font-size: 34px;
  color: var(--zp-primary-light);
}
.ai-item {
  display: flex;
  gap: 12px;
  font-size: 14px;
  line-height: 1.7;
}
.ai-label {
  flex-shrink: 0;
  color: var(--zp-primary);
  font-weight: 600;
  width: 80px;
}
.ai-value {
  color: #334155;
}

.detail-body {
  padding: 22px 24px;
}
.body-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.welfare-list {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.welfare-tag {
  padding: 6px 14px;
}
</style>
