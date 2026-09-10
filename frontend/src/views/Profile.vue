<template>
  <div class="zp-page">
    <h2 class="zp-page-title"><el-icon><User /></el-icon> 个人中心</h2>
    <p class="zp-page-sub">完善个人信息与求职期望，推荐算法将更加精准</p>

    <div class="profile-grid">
      <!-- 基本信息 -->
      <section class="p-card zp-card">
        <div class="p-card-title"><el-icon><UserFilled /></el-icon> 基本信息</div>
        <el-form :model="basic" label-width="96px" size="default">
          <el-form-item label="真实姓名">
            <el-input v-model="basic.real_name" placeholder="请输入真实姓名" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="basic.phone" placeholder="用于企业联系" />
          </el-form-item>
          <el-form-item label="性别">
            <el-radio-group v-model="basic.gender">
              <el-radio value="male">男</el-radio>
              <el-radio value="female">女</el-radio>
              <el-radio value="other">保密</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="生日">
            <el-date-picker v-model="basic.birthday" type="date" value-format="YYYY-MM-DD"
                            placeholder="选择日期" style="width: 100%" />
          </el-form-item>
          <el-form-item label="所在城市">
            <el-input v-model="basic.city" placeholder="如：北京" />
          </el-form-item>
          <el-form-item label="个人简介">
            <el-input v-model="basic.self_intro" type="textarea" :rows="3"
                      placeholder="一句话介绍自己，突出优势" />
          </el-form-item>
        </el-form>
      </section>

      <!-- 求职期望 -->
      <section class="p-card zp-card">
        <div class="p-card-title"><el-icon><Aim /></el-icon> 求职期望</div>
        <el-form :model="basic" label-width="96px" size="default">
          <el-form-item label="期望岗位">
            <el-input v-model="basic.expected_position" placeholder="如：Python开发工程师" />
          </el-form-item>
          <el-form-item label="期望城市">
            <el-input v-model="basic.expected_city" placeholder="如：北京" />
          </el-form-item>
          <el-form-item label="薪资期望">
            <div class="salary-range">
              <el-input-number v-model="basic.salary_min" :min="0" :max="200" placeholder="最低(K)" />
              <span>~</span>
              <el-input-number v-model="basic.salary_max" :min="0" :max="300" placeholder="最高(K)" />
              <span class="unit">K/月</span>
            </div>
          </el-form-item>
          <el-form-item label="工作年限">
            <el-input-number v-model="basic.experience_years" :min="0" :max="40" />
            <span class="unit" style="margin-left:8px">年</span>
          </el-form-item>
          <el-form-item label="学历">
            <el-select v-model="basic.education_level" placeholder="选择学历" style="width: 100%">
              <el-option v-for="e in ['高中', '大专', '本科', '硕士', '博士']" :key="e" :label="e" :value="e" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" class="zp-btn-gradient" :loading="saving" @click="saveBasic">保存资料</el-button>
          </el-form-item>
        </el-form>
      </section>
    </div>

    <div class="profile-grid">
      <!-- 技能特长 -->
      <section class="p-card zp-card">
        <div class="p-card-title">
          <el-icon><MagicStick /></el-icon> 技能特长
          <el-button size="small" text type="primary" @click="openSkillDialog"><el-icon><Plus /></el-icon> 添加</el-button>
        </div>
        <div class="skill-list">
          <div v-for="s in profile.skills || []" :key="s.id" class="skill-item">
            <span class="skill-name">{{ s.name }}</span>
            <el-rate :model-value="s.level" disabled size="small" />
            <el-button size="small" text type="danger" @click="removeSkill(s)"><el-icon><Delete /></el-icon></el-button>
          </div>
          <el-empty v-if="!(profile.skills || []).length" description="暂无技能" :image-size="60" />
        </div>
      </section>

      <!-- 教育背景 -->
      <section class="p-card zp-card">
        <div class="p-card-title">
          <el-icon><School /></el-icon> 教育背景
          <el-button size="small" text type="primary" @click="openEduDialog"><el-icon><Plus /></el-icon> 添加</el-button>
        </div>
        <div class="timeline">
          <div v-for="e in profile.educations || []" :key="e.id" class="tl-item">
            <div class="tl-main">
              <span class="tl-name">{{ e.school }}</span>
              <el-tag size="small" effect="plain">{{ e.degree || '学历' }}</el-tag>
            </div>
            <div class="tl-sub">{{ e.major || '-' }} · {{ e.start_date || '?' }} ~ {{ e.end_date || '至今' }}</div>
            <div class="tl-actions">
              <el-button size="small" text @click="editEdu(e)">编辑</el-button>
              <el-button size="small" text type="danger" @click="removeEdu(e)">删除</el-button>
            </div>
          </div>
          <el-empty v-if="!(profile.educations || []).length" description="暂无教育经历" :image-size="60" />
        </div>
      </section>
    </div>

    <!-- 工作经历 -->
    <section class="p-card zp-card">
      <div class="p-card-title">
        <el-icon><Briefcase /></el-icon> 工作经历
        <el-button size="small" text type="primary" @click="openWorkDialog"><el-icon><Plus /></el-icon> 添加</el-button>
      </div>
      <div class="work-list">
        <div v-for="w in profile.works || []" :key="w.id" class="work-item">
          <div class="work-head">
            <span class="work-company">{{ w.company }}</span>
            <span class="work-position">{{ w.position }}</span>
            <span class="work-date">{{ w.start_date || '?' }} ~ {{ w.end_date || '至今' }}</span>
          </div>
          <div class="work-desc">{{ w.description || '暂无描述' }}</div>
          <div class="tl-actions">
            <el-button size="small" text @click="editWork(w)">编辑</el-button>
            <el-button size="small" text type="danger" @click="removeWork(w)">删除</el-button>
          </div>
        </div>
        <el-empty v-if="!(profile.works || []).length" description="暂无工作经历" :image-size="60" />
      </div>
    </section>

    <!-- 修改密码 -->
    <section class="p-card zp-card">
      <div class="p-card-title"><el-icon><Lock /></el-icon> 修改密码</div>
      <el-form :model="pwd" label-width="96px" size="default" style="max-width: 420px">
        <el-form-item label="原密码">
          <el-input v-model="pwd.old" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwd.newp" type="password" show-password placeholder="8位以上，含字母数字特殊字符" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" plain @click="changePwd">确认修改</el-button>
        </el-form-item>
      </el-form>
    </section>

    <!-- 技能弹窗 -->
    <el-dialog v-model="skillDialog" title="添加技能" width="420px">
      <el-form label-width="70px">
        <el-form-item label="技能名称">
          <el-input v-model="skillForm.name" placeholder="如：Python" />
        </el-form-item>
        <el-form-item label="熟练度">
          <el-rate v-model="skillForm.level" :max="5" show-score />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="skillDialog = false">取消</el-button>
        <el-button type="primary" class="zp-btn-gradient" @click="addSkill">保存</el-button>
      </template>
    </el-dialog>

    <!-- 教育弹窗 -->
    <el-dialog v-model="eduDialog" :title="eduForm.id ? '编辑教育经历' : '添加教育经历'" width="480px">
      <el-form label-width="70px">
        <el-form-item label="学校"><el-input v-model="eduForm.school" /></el-form-item>
        <el-form-item label="专业"><el-input v-model="eduForm.major" /></el-form-item>
        <el-form-item label="学历">
          <el-select v-model="eduForm.degree" style="width: 100%">
            <el-option v-for="e in ['大专', '本科', '硕士', '博士']" :key="e" :label="e" :value="e" />
          </el-select>
        </el-form-item>
        <el-form-item label="起止时间">
          <div class="date-row">
            <el-input v-model="eduForm.start_date" placeholder="如2020-09" />
            <span>~</span>
            <el-input v-model="eduForm.end_date" placeholder="如2024-06或留空" />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="eduDialog = false">取消</el-button>
        <el-button type="primary" class="zp-btn-gradient" @click="saveEdu">保存</el-button>
      </template>
    </el-dialog>

    <!-- 工作弹窗 -->
    <el-dialog v-model="workDialog" :title="workForm.id ? '编辑工作经历' : '添加工作经历'" width="520px">
      <el-form label-width="70px">
        <el-form-item label="公司"><el-input v-model="workForm.company" /></el-form-item>
        <el-form-item label="职位"><el-input v-model="workForm.position" /></el-form-item>
        <el-form-item label="起止时间">
          <div class="date-row">
            <el-input v-model="workForm.start_date" placeholder="如2021-07" />
            <span>~</span>
            <el-input v-model="workForm.end_date" placeholder="如2024-06或留空" />
          </div>
        </el-form-item>
        <el-form-item label="工作内容">
          <el-input v-model="workForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="workDialog = false">取消</el-button>
        <el-button type="primary" class="zp-btn-gradient" @click="saveWork">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { userApi } from '../api'
import { useUserStore } from '../stores/user'

const store = useUserStore()
const profile = ref({ skills: [], educations: [], works: [] })
const saving = ref(false)
const basic = reactive({})

// 弹窗状态
const skillDialog = ref(false)
const skillForm = reactive({ name: '', level: 3 })
const eduDialog = ref(false)
const eduForm = reactive({ id: null, school: '', major: '', degree: '本科', start_date: '', end_date: '' })
const workDialog = ref(false)
const workForm = reactive({ id: null, company: '', position: '', start_date: '', end_date: '', description: '' })
const pwd = reactive({ old: '', newp: '' })

onMounted(loadProfile)

async function loadProfile() {
  try {
    const data = await userApi.getProfile()
    if (data) {
      profile.value = data
      Object.assign(basic, {
        real_name: data.real_name, phone: data.phone, gender: data.gender,
        birthday: data.birthday, city: data.city, self_intro: data.self_intro,
        expected_position: data.expected_position, expected_city: data.expected_city,
        salary_min: data.salary_min, salary_max: data.salary_max,
        experience_years: data.experience_years, education_level: data.education_level
      })
    }
  } catch (e) { /* handled */ }
}

async function saveBasic() {
  saving.value = true
  try {
    const data = await userApi.updateProfile(basic)
    profile.value = data
    store.setProfile(data)
    ElMessage.success('资料已保存')
  } finally {
    saving.value = false
  }
}

// ---------- 技能 ----------
function openSkillDialog() {
  skillForm.name = ''
  skillForm.level = 3
  skillDialog.value = true
}
async function addSkill() {
  if (!skillForm.name.trim()) return ElMessage.warning('请输入技能名称')
  await userApi.addSkill({ name: skillForm.name, level: skillForm.level })
  skillDialog.value = false
  loadProfile()
}
async function removeSkill(s) {
  await userApi.deleteSkill(s.id)
  loadProfile()
}

// ---------- 教育 ----------
function openEduDialog() {
  Object.assign(eduForm, { id: null, school: '', major: '', degree: '本科', start_date: '', end_date: '' })
  eduDialog.value = true
}
function editEdu(e) {
  Object.assign(eduForm, { ...e })
  eduDialog.value = true
}
async function saveEdu() {
  if (eduForm.id) await userApi.updateEducation(eduForm.id, eduForm)
  else await userApi.addEducation(eduForm)
  eduDialog.value = false
  loadProfile()
}
async function removeEdu(e) {
  await userApi.deleteEducation(e.id)
  loadProfile()
}

// ---------- 工作 ----------
function openWorkDialog() {
  Object.assign(workForm, { id: null, company: '', position: '', start_date: '', end_date: '', description: '' })
  workDialog.value = true
}
function editWork(w) {
  Object.assign(workForm, { ...w })
  workDialog.value = true
}
async function saveWork() {
  if (workForm.id) await userApi.updateWork(workForm.id, workForm)
  else await userApi.addWork(workForm)
  workDialog.value = false
  loadProfile()
}
async function removeWork(w) {
  await userApi.deleteWork(w.id)
  loadProfile()
}

async function changePwd() {
  if (!pwd.old || !pwd.newp) return ElMessage.warning('请填写完整')
  await userApi.changePassword({ old_password: pwd.old, new_password: pwd.newp })
  pwd.old = ''
  pwd.newp = ''
  ElMessage.success('密码修改成功')
}
</script>

<style scoped>
.profile-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.p-card {
  padding: 20px 24px;
  margin-bottom: 16px;
}
.p-card-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.salary-range {
  display: flex;
  align-items: center;
  gap: 8px;
}
.unit {
  color: var(--zp-text-secondary);
  font-size: 13px;
}
.skill-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.skill-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border: 1px solid var(--zp-border);
  border-radius: 10px;
}
.skill-name {
  font-weight: 600;
  min-width: 90px;
}
.timeline {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.tl-item {
  border: 1px solid var(--zp-border);
  border-radius: 10px;
  padding: 12px 14px;
}
.tl-main {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tl-name {
  font-weight: 600;
}
.tl-sub {
  font-size: 13px;
  color: var(--zp-text-secondary);
  margin-top: 4px;
}
.tl-actions {
  margin-top: 8px;
}
.work-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.work-item {
  border: 1px solid var(--zp-border);
  border-radius: 10px;
  padding: 12px 16px;
}
.work-head {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.work-company {
  font-weight: 700;
}
.work-position {
  color: var(--zp-primary);
  font-size: 13px;
}
.work-date {
  color: var(--zp-text-secondary);
  font-size: 12px;
  margin-left: auto;
}
.work-desc {
  font-size: 13px;
  color: #475569;
  margin-top: 8px;
  line-height: 1.7;
}
.date-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
@media (max-width: 900px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
