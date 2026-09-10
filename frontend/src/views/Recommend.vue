<template>
  <div class="zp-page">
    <h2 class="zp-page-title"><el-icon><DataAnalysis /></el-icon> 智能推荐</h2>
    <p class="zp-page-sub">基于技能、薪资期望、地点、经验与学历的多维匹配算法</p>

    <el-tabs v-if="store.isEnterprise" v-model="tab">
      <el-tab-pane label="岗位推荐" name="jobs">
        <job-recommend />
      </el-tab-pane>
      <el-tab-pane label="候选人匹配" name="candidates">
        <candidate-match />
      </el-tab-pane>
    </el-tabs>

    <job-recommend v-else />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useUserStore } from '../stores/user'
import JobRecommend from '../components/JobRecommend.vue'
import CandidateMatch from '../components/CandidateMatch.vue'

const store = useUserStore()
const tab = ref('jobs')
</script>
