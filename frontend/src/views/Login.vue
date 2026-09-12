<template>
  <div class="auth-page">
    <div class="auth-left">
      <div class="brand">
        <div class="brand-badge">智</div>
        <span class="brand-name">智聘通</span>
      </div>
      <h1 class="slogan">发现你的理想职业</h1>
      <p class="sub-slogan">智能爬取海量岗位 · AI 精准推荐 · 简历智能优化</p>
      <div class="feature-list">
        <div class="feature"><el-icon><DataAnalysis /></el-icon> 基于多维匹配度的智能岗位推荐</div>
        <div class="feature"><el-icon><ChatDotRound /></el-icon> DeepSeek AI 职业对话与简历优化</div>
        <div class="feature"><el-icon><Monitor /></el-icon> 多线程爬虫实时采集 前程无忧 职位</div>
        <div class="feature"><el-icon><Document /></el-icon> PDF / Word 简历解析，一键结构化</div>
      </div>
      <div class="auth-left-foot">2026 · 毕业设计项目 · Flask + Vue3 + DeepSeek</div>
    </div>

    <div class="auth-right">
      <div class="auth-card zp-card">
        <h2 class="card-title">欢迎回来 👋</h2>
        <p class="card-sub">登录你的智聘通账号</p>

        <el-form :model="form" @keyup.enter="onSubmit" size="large">
          <el-form-item>
            <el-input v-model="form.account" placeholder="用户名 / 邮箱" :prefix-icon="User" />
          </el-form-item>
          <el-form-item>
            <el-input v-model="form.password" type="password" placeholder="密码"
                      show-password :prefix-icon="Lock" />
          </el-form-item>
          <el-button type="primary" class="submit-btn zp-btn-gradient" :loading="loading"
                     @click="onSubmit">登 录</el-button>
        </el-form>

        <div class="auth-links">
          <router-link to="/register">没有账号？立即注册</router-link>
          <span class="demo-tip">演示账号：demo / Demo@123456</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'

const router = useRouter()
const store = useUserStore()
const form = reactive({ account: '', password: '' })
const loading = ref(false)

async function onSubmit() {
  if (!form.account || !form.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loading.value = true
  try {
    await store.login(form.account, form.password)
    await store.fetchMe()
    ElMessage.success('登录成功')
    router.push('/home')
  } catch (e) {
    // 错误已由拦截器提示
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  height: 100vh;
  display: flex;
}
.auth-left {
  flex: 1.2;
  background: linear-gradient(135deg, #1e1b4b 0%, #4f46e5 50%, #7c3aed 100%);
  color: #fff;
  padding: 56px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
}
.auth-left::after {
  content: '';
  position: absolute;
  right: -160px;
  top: -120px;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
}
.auth-left::before {
  content: '';
  position: absolute;
  left: -100px;
  bottom: -140px;
  width: 380px;
  height: 380px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 40px;
}
.brand-badge {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 700;
}
.brand-name {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 3px;
}
.slogan {
  font-size: 40px;
  font-weight: 800;
  margin: 0 0 12px;
  line-height: 1.3;
}
.sub-slogan {
  font-size: 16px;
  opacity: 0.85;
  margin: 0 0 40px;
}
.feature-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  z-index: 1;
}
.feature {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  opacity: 0.95;
}
.auth-left-foot {
  position: absolute;
  bottom: 24px;
  font-size: 12px;
  opacity: 0.6;
  z-index: 1;
}

.auth-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--zp-bg);
}
.auth-card {
  width: 400px;
  padding: 40px 36px;
}
.card-title {
  margin: 0 0 6px;
  font-size: 26px;
}
.card-sub {
  color: var(--zp-text-secondary);
  margin: 0 0 28px;
}
.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  letter-spacing: 4px;
  margin-top: 6px;
}
.auth-links {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  font-size: 13px;
}
.demo-tip {
  color: #94a3b8;
  font-size: 12px;
}
</style>
