<template>
  <div class="chat-page">
    <h2 class="zp-page-title"><el-icon><ChatDotRound /></el-icon> AI 职业助手</h2>
    <p class="zp-page-sub">由 DeepSeek 驱动 · 支持多轮上下文对话 · 可咨询求职建议、行业分析、面试技巧</p>

    <div class="chat-layout">
      <!-- 会话列表 -->
      <aside class="session-panel zp-card">
        <el-button type="primary" class="zp-btn-gradient new-btn" @click="newSession">
          <el-icon><Plus /></el-icon> 新对话
        </el-button>
        <div class="session-list">
          <div v-for="s in sessions" :key="s.id" class="session-item"
               :class="{ active: s.id === currentId }" @click="openSession(s)">
            <el-icon class="s-icon"><ChatLineSquare /></el-icon>
            <div class="s-info">
              <div class="s-title">{{ s.title }}</div>
              <div class="s-time">{{ fmtTime(s.updated_at) }}</div>
            </div>
            <el-icon class="s-del" @click.stop="removeSession(s)"><Close /></el-icon>
          </div>
        </div>
      </aside>

      <!-- 聊天区 -->
      <div class="chat-main zp-card">
        <div ref="msgBox" class="msg-list">
          <div v-if="!messages.length" class="welcome">
            <div class="w-avatar">智</div>
            <h3>你好，我是你的 AI 职业助手</h3>
            <p>我可以帮你分析职业方向、解读岗位、优化简历、准备面试</p>
            <div class="quick-tips">
              <div v-for="t in quickTips" :key="t" class="tip" @click="sendText(t)">{{ t }}</div>
            </div>
          </div>
          <div v-for="m in messages" :key="m.id" class="msg" :class="m.role">
            <div class="bubble">{{ m.content }}</div>
          </div>
          <div v-if="sending" class="msg assistant">
            <div class="bubble typing"><span></span><span></span><span></span></div>
          </div>
        </div>

        <div class="input-bar">
          <el-input v-model="inputText" type="textarea" :rows="2" resize="none"
                    placeholder="输入你的问题，如：帮我分析数据分析岗位的就业前景"
                    @keydown.enter.exact.prevent="send" />
          <el-button type="primary" class="zp-btn-gradient send-btn" :loading="sending"
                     :disabled="!inputText.trim() || !currentId" @click="send">
            <el-icon><Promotion /></el-icon> 发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { chatApi } from '../api'
import { toDate } from '../utils/date'

const sessions = ref([])
const currentId = ref(null)
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const msgBox = ref(null)

const quickTips = [
  '帮我分析Python开发工程师的就业前景',
  '我该学习哪些技能提升竞争力？',
  '给我一些面试技巧',
  '如何写一份优秀的简历？'
]

onMounted(async () => {
  sessions.value = await chatApi.listSessions()
  if (sessions.value.length) {
    await openSession(sessions.value[0])
  } else {
    await newSession()
  }
})

async function newSession() {
  const s = await chatApi.createSession({})
  sessions.value.unshift(s)
  await openSession(s)
}

async function openSession(s) {
  currentId.value = s.id
  messages.value = await chatApi.messages(s.id)
  scrollBottom()
}

async function removeSession(s) {
  await ElMessageBox.confirm('确定删除该对话？', '提示', { type: 'warning' })
  await chatApi.deleteSession(s.id)
  sessions.value = sessions.value.filter(x => x.id !== s.id)
  if (currentId.value === s.id) {
    if (sessions.value.length) await openSession(sessions.value[0])
    else await newSession()
  }
}

async function sendText(text) {
  inputText.value = text
  await send()
}

async function send() {
  const text = inputText.value.trim()
  if (!text || !currentId.value || sending.value) return
  inputText.value = ''
  // 乐观插入用户消息
  messages.value.push({ id: `t${Date.now()}`, role: 'user', content: text })
  sending.value = true
  scrollBottom()
  try {
    const data = await chatApi.send(currentId.value, text)
    messages.value.push({ id: `t${Date.now()}`, role: 'assistant', content: data.reply })
    const s = sessions.value.find(x => x.id === currentId.value)
    if (s) s.updated_at = new Date().toISOString()
  } catch (e) { /* handled */ } finally {
    sending.value = false
    scrollBottom()
  }
}

function scrollBottom() {
  nextTick(() => {
    if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
  })
}

function fmtTime(s) {
  const d = toDate(s)
  if (!d) return ''
  const pad = n => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
</script>

<style scoped>
.chat-layout {
  display: flex;
  gap: 16px;
  height: calc(100vh - 190px);
}
.session-panel {
  width: 240px;
  flex-shrink: 0;
  padding: 14px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.new-btn {
  width: 100%;
  margin-bottom: 12px;
}
.session-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
}
.session-item:hover {
  background: #f1f5f9;
}
.session-item.active {
  background: #eef2ff;
}
.s-icon {
  color: var(--zp-primary);
  flex-shrink: 0;
}
.s-info {
  flex: 1;
  min-width: 0;
}
.s-title {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.s-time {
  font-size: 11px;
  color: var(--zp-text-secondary);
}
.s-del {
  color: #94a3b8;
  opacity: 0;
}
.session-item:hover .s-del {
  opacity: 1;
}
.s-del:hover {
  color: #ef4444;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.msg-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.welcome {
  text-align: center;
  margin: auto;
  color: var(--zp-text-secondary);
  max-width: 480px;
}
.w-avatar {
  width: 56px;
  height: 56px;
  margin: 0 auto 12px;
  border-radius: 16px;
  background: var(--zp-gradient);
  color: #fff;
  font-size: 26px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.welcome h3 {
  margin: 0 0 8px;
  color: var(--zp-text);
}
.quick-tips {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 20px;
}
.tip {
  background: #f1f5f9;
  border: 1px solid var(--zp-border);
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.tip:hover {
  background: #eef2ff;
  border-color: var(--zp-primary-light);
  color: var(--zp-primary);
}

.msg {
  display: flex;
}
.msg.user {
  justify-content: flex-end;
}
.bubble {
  max-width: 72%;
  padding: 12px 16px;
  border-radius: 14px;
  line-height: 1.8;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}
.msg.assistant .bubble {
  background: #f1f5f9;
  border-top-left-radius: 4px;
}
.msg.user .bubble {
  background: var(--zp-gradient);
  color: #fff;
  border-top-right-radius: 4px;
}
.typing {
  display: flex;
  gap: 4px;
  padding: 16px;
}
.typing span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #94a3b8;
  animation: bounce 1.2s infinite;
}
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40% { transform: translateY(-6px); opacity: 1; }
}

.input-bar {
  border-top: 1px solid var(--zp-border);
  padding: 14px 16px;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}
.send-btn {
  height: 54px;
  padding: 0 22px;
}
</style>
