<template>
  <div class="zp-page analysis-page">
    <!-- 标题区 -->
    <section class="analysis-hero zp-card">
      <h2 class="zp-page-title"><el-icon><TrendCharts /></el-icon> 招聘市场数据分析</h2>
      <p class="zp-page-sub">基于岗位数据采集，洞察就业趋势</p>
    </section>

    <!-- 四宫格图表（岗位需求/Top5薪资 + 经验薪资/学历） -->
    <div class="chart-grid">
      <section class="chart-card zp-card">
        <h3 class="chart-title"><el-icon><Histogram /></el-icon> 岗位需求排行</h3>
        <div ref="demandRef" class="chart"></div>
      </section>
      <section class="chart-card zp-card">
        <h3 class="chart-title"><el-icon><Money /></el-icon> 岗位平均薪资</h3>
        <div ref="catSalaryRef" class="chart"></div>
      </section>
      <section class="chart-card zp-card">
        <h3 class="chart-title"><el-icon><Reading /></el-icon> 学历对薪资的影响</h3>
        <div ref="eduSalaryRef" class="chart"></div>
      </section>
      <section class="chart-card zp-card">
        <h3 class="chart-title"><el-icon><PieChart /></el-icon> 学历分布</h3>
        <div ref="eduRef" class="chart"></div>
      </section>
    </div>

    <!-- 地区平均薪资排行 -->
    <section class="chart-card zp-card span-full">
      <h3 class="chart-title"><el-icon><Location /></el-icon> 地区平均薪资排行</h3>
      <div ref="citySalaryRef" class="chart"></div>
    </section>

    <!-- AI 分析结论 -->
    <section class="conclusion-card zp-card" v-loading="loading">
      <h3 class="chart-title"><el-icon><MagicStick /></el-icon> AI 分析结论</h3>
      <ul class="conclusion-list">
        <li v-for="(c, i) in conclusions" :key="i">
          <span class="dot"></span>{{ c }}
        </li>
      </ul>
      <el-empty v-if="!loading && conclusions.length === 0" description="暂无数据" />
    </section>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { jobApi } from '../api'

const loading = ref(false)
const conclusions = ref([])
const demandRef = ref(null)
const catSalaryRef = ref(null)
const eduSalaryRef = ref(null)
const citySalaryRef = ref(null)
const eduRef = ref(null)
let charts = []

const palette = ['#4f46e5', '#818cf8', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#8b5cf6', '#f43f5e']

function initChart(el) {
  const chart = echarts.init(el)
  charts.push(chart)
  return chart
}

function render(data) {
  const demand = echarts.init(demandRef.value)
  charts.push(demand)
  demand.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 10, right: 20, top: 20, bottom: 8, containLabel: true },
    xAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: '#f1f5f9' } } },
    yAxis: { type: 'category', data: data.demand_rank.map(d => d.category),
             inverse: true, axisLine: { show: false }, axisTick: { show: false } },
    series: [{
      type: 'bar', barMaxWidth: 22, data: data.demand_rank.map(d => d.count),
      itemStyle: { color: '#4f46e5', borderRadius: [0, 6, 6, 0] },
      label: { show: true, position: 'right' }
    }]
  })

  const catSalary = echarts.init(catSalaryRef.value)
  charts.push(catSalary)
  catSalary.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
               formatter: params => `${params[0].name}<br/>平均月薪：${params[0].value}K` },
    grid: { left: 10, right: 30, top: 20, bottom: 8, containLabel: true },
    xAxis: { type: 'value', name: 'K/月', nameLocation: 'end', nameGap: 6, nameTextStyle: { color: '#64748b', fontSize: 11 },
             splitLine: { lineStyle: { color: '#f1f5f9' } } },
    yAxis: { type: 'category', data: data.category_salary.map(d => d.category),
             inverse: true, axisLine: { show: false }, axisTick: { show: false } },
    series: [{
      type: 'bar', barMaxWidth: 20, data: data.category_salary.map(d => d.avg),
      itemStyle: { color: '#10b981', borderRadius: [0, 6, 6, 0] },
      label: { show: true, position: 'right', formatter: '{c}K' }
    }]
  })

  const eduSalary = echarts.init(eduSalaryRef.value)
  charts.push(eduSalary)
  eduSalary.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
               formatter: params => `${params[0].name}<br/>平均月薪：${params[0].value}K` },
    grid: { left: 10, right: 20, top: 30, bottom: 24, containLabel: true },
    xAxis: { type: 'category', data: data.education_salary.map(d => d.education),
             axisLine: { show: false }, axisTick: { show: false },
             axisLabel: { interval: 0, rotate: 20, color: '#64748b' } },
    yAxis: { type: 'value', name: 'K/月', nameLocation: 'end', nameGap: 12, nameTextStyle: { color: '#64748b', fontSize: 11 },
             splitLine: { lineStyle: { color: '#f1f5f9' } } },
    series: [{
      type: 'bar', barMaxWidth: 26, data: data.education_salary.map(d => d.avg),
      itemStyle: { color: '#8b5cf6', borderRadius: [6, 6, 0, 0] },
      label: { show: true, position: 'top', formatter: '{c}K' }
    }]
  })

  const edu = echarts.init(eduRef.value)
  charts.push(edu)
  edu.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0 },
    color: palette,
    series: [{
      type: 'pie', radius: ['45%', '68%'], center: ['50%', '46%'],
      label: { formatter: '{b}\n{d}%' },
      data: data.education_dist
    }]
  })

  const citySalary = echarts.init(citySalaryRef.value)
  charts.push(citySalary)
  citySalary.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
               formatter: params => `${params[0].name}<br/>平均月薪：${params[0].value}K` },
    grid: { left: 10, right: 20, top: 30, bottom: 24, containLabel: true },
    xAxis: { type: 'category', data: data.city_salary.map(d => d.city),
             axisLine: { show: false }, axisTick: { show: false },
             axisLabel: { interval: 0, rotate: 30, color: '#64748b' } },
    yAxis: { type: 'value', name: 'K/月', nameLocation: 'end', nameGap: 12, nameTextStyle: { color: '#64748b', fontSize: 11 },
             splitLine: { lineStyle: { color: '#f1f5f9' } } },
    series: [{
      type: 'bar', barMaxWidth: 26, data: data.city_salary.map(d => d.avg),
      itemStyle: { color: '#f59e0b', borderRadius: [6, 6, 0, 0] },
      label: { show: true, position: 'top', formatter: '{c}K' }
    }]
  })
}

function handleResize() {
  charts.forEach(c => c.resize())
}

onMounted(async () => {
  loading.value = true
  try {
    const data = await jobApi.analysis()
    render(data)
    conclusions.value = data.conclusions || []
  } catch (e) {
    /* ignore */
  } finally {
    loading.value = false
  }
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  charts.forEach(c => c.dispose())
  charts = []
})
</script>

<style scoped>
.analysis-page {
  padding: 16px;
}
.analysis-hero {
  padding: 20px;
  margin-bottom: 16px;
}
.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.chart-card {
  padding: 20px;
}
.chart-card.span-full {
  grid-column: 1 / -1;
  margin-top: 16px;
}
.chart-title {
  margin: 0 0 12px;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.chart {
  height: 300px;
}
.conclusion-card {
  margin-top: 16px;
  padding: 20px;
}
.conclusion-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.conclusion-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--zp-border);
  color: var(--zp-text-secondary);
  font-size: 14px;
}
.conclusion-list li:last-child {
  border-bottom: none;
}
.dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  margin-top: 6px;
  border-radius: 50%;
  background: var(--zp-gradient);
}
@media (max-width: 900px) {
  .chart-grid {
    grid-template-columns: 1fr;
  }
}
</style>