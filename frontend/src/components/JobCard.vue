<template>
  <div class="job-card zp-card" @click="$emit('click', job)">
    <div class="job-main">
      <div class="job-info">
        <div class="job-title-row">
          <h3 class="job-title">{{ job.title }}</h3>
          <el-tag v-if="job.source === 'crawler'" size="small" type="success" effect="light">爬取</el-tag>
          <el-tag v-else-if="job.source === 'mock'" size="small" type="info" effect="light">模拟</el-tag>
          <el-tag v-else size="small" type="info" effect="plain">内置</el-tag>
        </div>
        <div class="job-meta">
          <span class="meta-item"><el-icon><LocationInformation /></el-icon>{{ job.city }}{{ job.district }}</span>
          <span v-if="job.experience_required" class="meta-item"><el-icon><Briefcase /></el-icon>{{ job.experience_required }}</span>
          <span v-if="job.education_required" class="meta-item"><el-icon><Reading /></el-icon>{{ job.education_required }}</span>
        </div>
        <div class="job-tags">
          <el-tag v-for="t in (job.job_tags || []).slice(0, 4)" :key="t" size="small" effect="plain" class="tag">{{ t }}</el-tag>
        </div>
      </div>
      <div class="job-side">
        <div class="salary">{{ job.salary_text }}</div>
        <div class="company">{{ job.company_name }}</div>
      </div>
    </div>
    <div class="job-foot">
      <span class="source-link" @click.stop>
        <el-link v-if="job.link" type="primary" :underline="false" @click.stop="openSource">
          <el-icon><Position /></el-icon>查看原文
        </el-link>
      </span>
      <span class="fav" @click.stop>
        <el-button size="small" text :type="job.is_favorite ? 'danger' : ''"
                   @click="$emit('favorite', job)">
          <el-icon><StarFilled v-if="job.is_favorite" /><Star v-else /></el-icon>
          {{ job.is_favorite ? '已收藏' : '收藏' }}
        </el-button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  job: { type: Object, required: true }
})
defineEmits(['click', 'favorite'])
const router = useRouter()

function openSource() {
  if (props.job.link) {
    window.open(props.job.link, '_blank')
  }
}
</script>

<style scoped>
.job-card {
  padding: 18px 20px;
  cursor: pointer;
}
.job-card:hover {
  border-color: var(--zp-primary-light);
}
.job-main {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}
.job-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.job-title {
  font-size: 16px;
  margin: 0;
  color: var(--zp-text);
}
.job-meta {
  display: flex;
  gap: 14px;
  margin-top: 8px;
  color: var(--zp-text-secondary);
  font-size: 13px;
  flex-wrap: wrap;
}
.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.job-tags {
  margin-top: 10px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.tag {
  background: #eef2ff;
  color: var(--zp-primary);
  border: none;
}
.job-side {
  text-align: right;
  flex-shrink: 0;
}
.salary {
  color: #f59e0b;
  font-size: 18px;
  font-weight: 700;
}
.company {
  color: var(--zp-text-secondary);
  font-size: 13px;
  margin-top: 8px;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.job-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed var(--zp-border);
}
</style>
