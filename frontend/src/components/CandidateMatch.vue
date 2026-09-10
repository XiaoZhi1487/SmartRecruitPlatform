<template>
  <div class="match">
    <div class="pick-row">
      <el-select v-model="selectedJobId" filterable placeholder="选择职位以匹配候选人" style="width: 320px"
                 :loading="jobsLoading" @visible-change="loadJobsIfEmpty">
        <el-option v-for="j in jobs" :key="j.id" :label="`${j.title} @ ${j.company_name} · ${j.salary_text}`"
                   :value="j.id" />
      </el-select>
      <el-button type="primary" class="zp-btn-gradient" :loading="loading"
                 :disabled="!selectedJobId" @click="load">开始匹配</el-button>
    </div>

    <div v-loading="loading" class="match-list">
      <div v-for="c in candidates" :key="c.user_id" class="match-card zp-card">
        <div class="mc-score">
          <el-progress type="circle" :percentage="c.match_score" :width="60" :stroke-width="8" color="#059669" />
          <span class="score-label">匹配度</span>
        </div>
        <div class="mc-info">
          <div class="mc-name">{{ c.real_name || c.username }}</div>
          <div class="mc-meta">
            {{ c.education_level || '学历未知' }} · {{ c.experience_years ?? '-' }}年经验 ·
            {{ c.city || '城市未知' }} · 期望：{{ c.expected_position || '-' }}
          </div>
          <div class="mc-skills">
            <el-tag v-for="s in (c.skills || []).slice(0, 6)" :key="s" size="small" effect="plain">{{ s }}</el-tag>
          </div>
          <div class="mc-dims">
            <span v-for="(v, k) in c.dimensions" :key="k" class="dim">
              {{ dimLabel[k] }} <b :class="v >= 60 ? 'high' : v >= 40 ? 'mid' : 'low'">{{ v }}</b>
            </span>
          </div>
        </div>
      </div>
      <el-empty v-if="!loading && !candidates.length && searched" description="暂无匹配候选人" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { jobApi, recommendApi } from '../api'

const jobs = ref([])
const jobsLoading = ref(false)
const selectedJobId = ref(null)
const candidates = ref([])
const loading = ref(false)
const searched = ref(false)
const dimLabel = { skill: '技能', salary: '薪资', location: '地点', experience: '经验', education: '学历' }

async function loadJobsIfEmpty(visible) {
  if (!visible || jobs.value.length) return
  jobsLoading.value = true
  try {
    const data = await jobApi.list({ page: 1, page_size: 50, sort: 'latest' })
    jobs.value = data.items
  } finally {
    jobsLoading.value = false
  }
}

async function load() {
  loading.value = true
  searched.value = true
  try {
    const data = await recommendApi.candidates({ job_id: selectedJobId.value, limit: 30 })
    candidates.value = data.items
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.pick-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.match-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 160px;
}
.match-card {
  display: flex;
  gap: 20px;
  padding: 18px 22px;
}
.mc-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}
.score-label {
  font-size: 12px;
  color: var(--zp-text-secondary);
}
.mc-info {
  flex: 1;
  min-width: 0;
}
.mc-name {
  font-size: 16px;
  font-weight: 700;
}
.mc-meta {
  color: var(--zp-text-secondary);
  font-size: 13px;
  margin-top: 6px;
}
.mc-skills {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.mc-dims {
  display: flex;
  gap: 14px;
  margin-top: 10px;
  font-size: 12px;
  color: var(--zp-text-secondary);
  flex-wrap: wrap;
}
.dim .high { color: #16a34a; }
.dim .mid { color: #d97706; }
.dim .low { color: #dc2626; }
</style>
