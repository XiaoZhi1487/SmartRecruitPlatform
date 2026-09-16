<template>
  <div class="recommend">
    <!-- 用户画像提示 -->
    <div class="ctx-tip zp-card" v-if="overview && overview.suggestion">
      <el-icon><InfoFilled /></el-icon>
      <span>{{ overview.suggestion }}</span>
      <el-link type="primary" @click="$router.push('/profile')">去完善画像 →</el-link>
    </div>

    <!-- 热门技能 -->
    <section class="hot-skills zp-card" v-if="(overview?.hot_skills || []).length">
      <div class="hs-title">平台热门技能</div>
      <div class="hs-tags">
        <el-tag v-for="s in overview.hot_skills.slice(0, 12)" :key="s.name"
                size="small" effect="plain" class="hs-tag">{{ s.name }} · {{ s.count }}</el-tag>
      </div>
    </section>

    <!-- 动态权重说明 -->
    <section class="weight-card zp-card" v-if="weights">
      <div class="hs-title">动态自适应权重（行为反馈学习）</div>
      <div class="w-row">
        <span v-for="d in dimList" :key="d.k" class="w-item">
          {{ d.label }}
          <el-tag size="small" class="w-tag" :class="{ hot: !d.personal }">{{ d.v }}%</el-tag>
        </span>
      </div>
      <div class="w-note">
        <el-icon><MagicStick /></el-icon>
        权重由平台岗位数据区分度与你的浏览/详情/收藏/投递行为动态生成；
        {{ weights.using_personal ? '已启用个性化调节。' : '当前为全局权重（行为数据积累后将转为个性化）。' }}
      </div>
    </section>

    <!-- 推荐列表 -->
    <div v-loading="loading" class="rec-list">
      <div v-for="item in items" :key="item.id" class="rec-card zp-card" @click="goDetail(item)">
        <div class="rec-score">
          <el-progress type="circle" :percentage="item.match_score" :width="64" :stroke-width="8"
                       color="#4f46e5" />
          <span class="score-label">匹配度</span>
        </div>
        <div class="rec-info">
          <div class="rec-title">
            <h3>{{ item.title }}</h3>
            <span class="rec-salary">{{ item.salary_text }}</span>
          </div>
          <div class="rec-company">{{ item.company_name }} · {{ item.city }}{{ item.district }}</div>
          <div class="rec-tags">
            <el-tag v-for="t in (item.job_tags || []).slice(0, 4)" :key="t" size="small" effect="plain">{{ t }}</el-tag>
          </div>
          <div class="rec-reason"><el-icon><MagicStick /></el-icon> {{ item.reason }}</div>
          <div class="rec-dims">
            <span v-for="(v, k) in item.dimensions" :key="k" class="dim">
              {{ dimLabel[k] }} <b :class="v >= 60 ? 'high' : v >= 40 ? 'mid' : 'low'">{{ v }}</b>
            </span>
          </div>
        </div>
      </div>
      <el-empty v-if="!loading && items.length === 0" description="暂无推荐，请先完善个人画像" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { recommendApi } from '../api'

const router = useRouter()
const items = ref([])
const overview = ref(null)
const loading = ref(false)
const weights = ref(null)

const dimLabel = { skill: '技能', salary: '薪资', location: '地点', experience: '经验', education: '学历' }
const dimList = [
  { k: 'skill', label: '技能', v: 0 }, { k: 'salary', label: '薪资', v: 0 },
  { k: 'location', label: '地点', v: 0 }, { k: 'experience', label: '经验', v: 0 },
  { k: 'education', label: '学历', v: 0 },
]

function trackFeedback(item, action) {
  recommendApi.feedback({ job_id: item.id, action }).catch(() => {})
}

onMounted(async () => {
  loading.value = true
  try {
    const [rec, ov] = await Promise.all([recommendApi.jobs({ limit: 15 }), recommendApi.overview()])
    items.value = rec.items
    overview.value = ov
    if (rec.weights) {
      const w = rec.weights.weights
      dimList.forEach(d => { d.v = Math.round(w[d.k] * 100) })
      weights.value = rec.weights
    }
  } finally {
    loading.value = false
  }
})

function goDetail(item) {
  trackFeedback(item, 'view')
  router.push(`/job/${item.id}`)
}
</script>

<style scoped>
.ctx-tip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  margin-bottom: 14px;
  color: var(--zp-text-secondary);
  font-size: 14px;
}
.hot-skills {
  padding: 16px 20px;
  margin-bottom: 14px;
}
.hs-title {
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 10px;
}
.weight-card {
  padding: 16px 20px;
  margin-bottom: 14px;
}
.w-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.w-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--zp-text-secondary);
}
.w-tag.hot {
  background: #f59e0b;
  border-color: #f59e0b;
  color: #fff;
}
.w-note {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
}
.hs-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.hs-tag {
  background: #eef2ff;
  color: var(--zp-primary);
  border: none;
}
.rec-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 200px;
}
.rec-card {
  display: flex;
  gap: 20px;
  padding: 18px 22px;
  cursor: pointer;
}
.rec-card:hover {
  border-color: var(--zp-primary-light);
}
.rec-score {
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
.rec-info {
  flex: 1;
  min-width: 0;
}
.rec-title {
  display: flex;
  align-items: center;
  gap: 12px;
}
.rec-title h3 {
  margin: 0;
  font-size: 16px;
}
.rec-salary {
  color: #f59e0b;
  font-weight: 700;
}
.rec-company {
  color: var(--zp-text-secondary);
  font-size: 13px;
  margin-top: 6px;
}
.rec-tags {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.rec-reason {
  margin-top: 10px;
  font-size: 13px;
  color: var(--zp-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}
.rec-dims {
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
