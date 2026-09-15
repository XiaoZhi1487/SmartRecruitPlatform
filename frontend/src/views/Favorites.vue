<template>
  <div class="zp-page">
    <div class="fav-head zp-card">
      <div>
        <h2 class="zp-page-title"><el-icon><StarFilled /></el-icon> 我的收藏</h2>
        <p class="zp-page-sub">共 {{ total }} 个收藏职位，点击收藏按钮可取消收藏</p>
      </div>
      <el-button :icon="Refresh" @click="load" v-loading="loading">刷新</el-button>
    </div>

    <div class="job-list" v-loading="loading">
      <JobCard v-for="job in jobs" :key="job.id" :job="job"
               @click="goDetail(job.id)"
               @favorite="unfavorite(job)" />
      <el-empty v-if="!loading && jobs.length === 0" description="还没有收藏职位">
        <el-button type="primary" class="zp-btn-gradient" @click="$router.push('/home')">
          去职位大厅逛逛
        </el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import JobCard from '../components/JobCard.vue'
import { jobApi } from '../api'

const router = useRouter()
const jobs = ref([])
const total = ref(0)
const loading = ref(false)

onMounted(load)

async function load() {
  loading.value = true
  try {
    const data = await jobApi.favorites()
    jobs.value = data.map(j => ({ ...j, is_favorite: true }))
    total.value = data.length
  } finally {
    loading.value = false
  }
}

async function unfavorite(job) {
  try {
    await jobApi.unfavorite(job.id)
    ElMessage.success('已取消收藏')
    jobs.value = jobs.value.filter(j => j.id !== job.id)
    total.value = jobs.value.length
  } catch (e) { /* ignore */ }
}

function goDetail(id) {
  router.push(`/job/${id}`)
}
</script>

<style scoped>
.fav-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  margin-bottom: 14px;
}
.job-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 200px;
}
</style>
