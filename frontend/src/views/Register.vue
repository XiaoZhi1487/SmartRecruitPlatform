<template>
  <div class="auth-page">
    <div class="auth-left">
      <div class="brand">
        <div class="brand-badge">智</div>
        <span class="brand-name">智聘通</span>
      </div>
      <h1 class="slogan">开启你的求职加速之旅</h1>
      <p class="sub-slogan">创建账号，享受 AI 驱动的智能求职体验</p>
      <div class="feature-list">
        <div class="feature"><el-icon><DataAnalysis /></el-icon> 个性化岗位智能推荐</div>
        <div class="feature"><el-icon><ChatDotRound /></el-icon> AI 简历优化与职业咨询</div>
        <div class="feature"><el-icon><Document /></el-icon> 简历一键解析，自动提取技能</div>
      </div>
    </div>

    <div class="auth-right">
      <div class="auth-card zp-card">
        <h2 class="card-title">创建账号</h2>
        <p class="card-sub">注册即享全部 AI 功能</p>

        <el-form :model="form" size="large">
          <el-form-item>
            <el-input v-model="form.username" placeholder="用户名（2-32位）" :prefix-icon="User" />
          </el-form-item>
          <el-form-item>
            <el-input v-model="form.email" placeholder="邮箱（用于验证）" :prefix-icon="Message" />
          </el-form-item>
          <el-form-item>
            <el-input v-model="form.password" type="password" placeholder="密码（8位以上，含字母数字特殊字符）"
                      show-password :prefix-icon="Lock" />
          </el-form-item>
          <div class="strength">
            <div class="strength-bar">
              <div class="bar-fill" :style="{ width: strength.percent + '%', background: strength.color }"></div>
            </div>
            <span class="strength-text" :style="{ color: strength.color }">{{ strength.label }}</span>
          </div>
          <el-form-item>
            <el-input v-model="form.confirm" type="password" placeholder="确认密码"
                      show-password :prefix-icon="Lock" />
          </el-form-item>
          <el-button type="primary" class="submit-btn zp-btn-gradient" :loading="loading"
                     @click="onSubmit">注 册</el-button>
        </el-form>

        <div class="auth-links">
          <router-link to="/login">已有账号？去登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { authApi } from '../api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const store = useUserStore()
const form = reactive({ username: '', email: '', password: '', confirm: '' })
const loading = ref(false)

const strength = computed(() => {
  const pwd = form.password
  let score = 0
  if (pwd.length >= 8) score += 25
  if (/[A-Za-z]/.test(pwd)) score += 25
  if (/\d/.test(pwd)) score += 25
  if (/[^A-Za-z0-9]/.test(pwd)) score += 25
  if (!pwd) score = 0
  const map = [
    { color: '#ef4444', label: '太弱' },
    { color: '#f97316', label: '较弱' },
    { color: '#eab308', label: '中等' },
    { color: '#22c55e', label: '较强' },
    { color: '#16a34a', label: '很强' }
  ]
  const idx = Math.min(4, Math.floor(score / 25))
  return { percent: score, color: map[idx].color, label: map[idx].label }
})

async function onSubmit() {
  if (!form.username || !form.email || !form.password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  if (form.password !== form.confirm) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    const data = await authApi.register({
      username: form.username, email: form.email, password: form.password
    })
    store.setToken(data.tokens.access_token)
    store.user = data.user
    ElMessage.success('注册成功，欢迎加入智聘通！')
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
}
.feature {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
}
.auth-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--zp-bg);
}
.auth-card {
  width: 440px;
  padding: 36px;
}
.card-title {
  margin: 0 0 6px;
  font-size: 26px;
}
.card-sub {
  color: var(--zp-text-secondary);
  margin: 0 0 24px;
}
.strength {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: -6px 0 18px;
}
.strength-bar {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  transition: all 0.3s;
}
.strength-text {
  font-size: 12px;
  width: 40px;
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
  text-align: center;
  font-size: 13px;
}
</style>
