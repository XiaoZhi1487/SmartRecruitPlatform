<template>
  <div class="zp-page">
    <!-- Hero -->
    <section class="hero zp-card">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <h1 class="hero-title">发现你的理想职业</h1>
        <p class="hero-sub">海量优质岗位 · AI 精准推荐 · 一键直达原文</p>
        <div class="search-row">
          <el-input v-model="query.keyword" placeholder="输入职位关键词，如：Python、数据分析"
                    class="search-input" :prefix-icon="Search" clearable
                    @keyup.enter="search" />
          <el-select v-model="query.city" placeholder="不限城市" clearable class="city-select">
            <el-option v-for="c in cities" :key="c" :label="c" :value="c" />
          </el-select>
          <el-button type="primary" class="zp-btn-gradient search-btn" @click="search">
            <el-icon><Search /></el-icon> 搜索职位
          </el-button>
        </div>
      </div>
      <div class="hero-stats">
        <div class="stat" v-for="s in heroStats" :key="s.label">
          <div class="stat-num">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>
    </section>

    <!-- 筛选 -->
    <div class="filter-bar zp-card">
      <div class="sort-group">
        <span class="sort-label">排序：</span>
        <el-radio-group v-model="query.sort" @change="search">
          <el-radio-button label="latest">最新发布</el-radio-button>
          <el-radio-button label="salary">薪资优先</el-radio-button>
        </el-radio-group>
      </div>
      <span class="total-tip">共 {{ total }} 个职位</span>
    </div>

    <!-- 职位列表 -->
    <div class="job-list" v-loading="loading">
      <JobCard v-for="job in jobs" :key="job.id" :job="job"
               @click="goDetail(job.id)"
               @favorite="toggleFavorite(job)" />
      <el-empty v-if="!loading && jobs.length === 0" description="未找到相关职位" />
    </div>

    <div class="pager" v-if="total > pageSize">
      <el-pagination background layout="prev, pager, next" :total="total"
                     :page-size="pageSize" :current-page="page" @current-change="onPage" />
    </div>

    <!-- 薪资分析 -->
    <section class="chart-section zp-card" v-if="salaryData.length">
      <h3 class="chart-title"><el-icon><TrendCharts /></el-icon> 各城市平均薪资（K/月）</h3>
      <div ref="chartRef" class="chart"></div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { Search } from '@element-plus/icons-vue'
import JobCard from '../components/JobCard.vue'
import { jobApi } from '../api'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const jobs = ref([])
const cities = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(false)
const heroStats = ref([
  { label: '在招职位', value: '-' },
  { label: '入驻公司', value: '-' },
  { label: '覆盖城市', value: '-' }
])
const salaryData = ref([])
const chartRef = ref(null)
let chart = null

const query = reactive({ keyword: '', city: '', sort: 'latest' })

onMounted(async () => {
  query.keyword = route.query.keyword || ''
  await Promise.all([loadJobs(), loadCities(), loadStats()])
})

async function loadJobs() {
  loading.value = true
  try {
    const data = await jobApi.list({ ...query, page: page.value, page_size: pageSize })
    jobs.value = data.items.map(j => ({ ...j, is_favorite: false }))
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadCities() {
  cities.value = await jobApi.cities()
}

async function loadStats() {
  try {
    const data = await jobApi.stats()
    heroStats.value = [
      { label: '在招职位', value: data.total_jobs },
      { label: '覆盖城市', value: data.city_salary.length },
      { label: '热门公司', value: data.top_companies.length }
    ]
    salaryData.value = data.city_salary || []
    renderChart()
  } catch (e) { /* ignore */ }
}

function renderChart() {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['平均最低', '平均最高'] },
    grid: { left: 40, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: salaryData.value.map(d => d.city) },
    yAxis: { type: 'value', name: 'K/月' },
    series: [
      { name: '平均最低', type: 'bar', data: salaryData.value.map(d => d.avg_min),
        itemStyle: { color: '#818cf8', borderRadius: [4, 4, 0, 0] }, barWidth: 18 },
      { name: '平均最高', type: 'bar', data: salaryData.value.map(d => d.avg_max),
        itemStyle: { color: '#4f46e5', borderRadius: [4, 4, 0, 0] }, barWidth: 18 }
    ]
  })
}

function search() {
  page.value = 1
  loadJobs()
}

function onPage(p) {
  page.value = p
  loadJobs()
  window.scrollTo({ top: 400, behavior: 'smooth' })
}

function goDetail(id) {
  router.push(`/job/${id}`)
}

async function toggleFavorite(job) {
  if (!store.isLoggedIn) {
    router.push('/login')
    return
  }
  if (job.is_favorite) {
    await jobApi.unfavorite(job.id)
    job.is_favorite = false
  } else {
    await jobApi.favorite(job.id)
    job.is_favorite = true
  }
}
</script>

<style scoped>
.hero {
  position: relative;
  overflow: hidden;
  padding: 44px 40px;
  margin-bottom: 16px;
  background: linear-gradient(120deg, #eef2ff 0%, #ede9fe 60%, #eff6ff 100%);
}
.hero-bg {
  position: absolute;
  right: -60px;
  top: -80px;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(124, 58, 237, 0.15), transparent 70%);
}
.hero-content {
  position: relative;
  z-index: 1;
}
.hero-title {
  font-size: 30px;
  font-weight: 800;
  margin: 0 0 8px;
}
.hero-sub {
  color: var(--zp-text-secondary);
  margin: 0 0 24px;
}
.search-row {
  display: flex;
  gap: 10px;
  max-width: 760px;
}
.search-input {
  flex: 1;
}
.search-input :deep(.el-input__wrapper) {
  border-radius: 10px;
}
.city-select {
  width: 140px;
}
.search-btn {
  height: 40px;
  padding: 0 28px;
  border-radius: 10px;
}
.hero-stats {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 48px;
  margin-top: 32px;
}
.stat-num {
  font-size: 26px;
  font-weight: 800;
  color: var(--zp-primary);
}
.stat-label {
  color: var(--zp-text-secondary);
  font-size: 13px;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  margin-bottom: 14px;
}
.sort-label {
  color: var(--zp-text-secondary);
  font-size: 13px;
  margin-right: 4px;
}
.total-tip {
  color: var(--zp-text-secondary);
  font-size: 13px;
}

.job-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 200px;
}
.pager {
  display: flex;
  justify-content: center;
  margin: 20px 0;
}

.chart-section {
  margin-top: 20px;
  padding: 20px;
}
.chart-title {
  margin: 0 0 16px;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.chart {
  height: 300px;
}
</style>
