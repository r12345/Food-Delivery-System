<template>
  <div class="login-wrap">
    <div class="login-card">
      <div class="title">乐享外卖</div>
      <el-tabs v-model="tab" stretch>
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" @keyup.enter="doLogin">
            <el-form-item>
              <el-input v-model="loginForm.username" placeholder="用户名" size="large" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="loginForm.password" type="password" show-password placeholder="密码" size="large" />
            </el-form-item>
            <el-form-item>
              <div class="captcha-row">
                <el-input v-model="loginForm.captcha_code" placeholder="验证码" size="large" />
                <img v-if="captcha" :src="captcha" class="captcha-img" title="点击刷新" @click="loadCaptcha" />
              </div>
            </el-form-item>
            <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="doLogin">登 录</el-button>
            <div class="tips">
              <el-link type="info" @click="forgotVisible = true">忘记密码</el-link>
              <span class="text-muted">演示：user1/123456 · merchant1/123456 · admin/admin123</span>
            </div>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form :model="regForm">
            <el-form-item>
              <el-radio-group v-model="regForm.role">
                <el-radio-button value="user">我是顾客</el-radio-button>
                <el-radio-button value="merchant">我要开店</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item v-if="regForm.role === 'merchant'">
              <el-input v-model="regForm.shop_name" placeholder="店铺名称" size="large" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="regForm.username" placeholder="用户名" size="large" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="regForm.phone" placeholder="手机号" size="large" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="regForm.password" type="password" show-password placeholder="密码(至少6位)" size="large" />
            </el-form-item>
            <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="doRegister">注 册</el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog v-model="forgotVisible" title="重置密码" width="400px">
      <el-form :model="forgotForm" label-width="80px">
        <el-form-item label="用户名"><el-input v-model="forgotForm.username" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="forgotForm.phone" /></el-form-item>
        <el-form-item label="新密码"><el-input v-model="forgotForm.new_password" type="password" show-password /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="forgotVisible = false">取消</el-button>
        <el-button type="primary" @click="doForgot">重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuth } from '../../stores/auth'
import { useCart } from '../../stores/cart'
import { getCaptcha, login, register, forgotPassword } from '../../api'

const router = useRouter()
const auth = useAuth()
const cart = useCart()
const tab = ref('login')
const loading = ref(false)
const captcha = ref('')
const forgotVisible = ref(false)

const loginForm = reactive({ username: '', password: '', captcha_id: '', captcha_code: '' })
const regForm = reactive({ role: 'user', username: '', password: '', phone: '', shop_name: '' })
const forgotForm = reactive({ username: '', phone: '', new_password: '' })

async function loadCaptcha() {
  const res = await getCaptcha()
  captcha.value = res.image
  loginForm.captcha_id = res.captcha_id
  loginForm.captcha_code = ''
}

function goHome(user) {
  if (user.role === 'merchant') return router.push('/merchant')
  if (user.role === 'admin') return router.push('/admin')
  cart.refresh()
  router.push('/')
}

async function doLogin() {
  if (!loginForm.username || !loginForm.password || !loginForm.captcha_code)
    return ElMessage.warning('请填写完整登录信息')
  loading.value = true
  try {
    const res = await login({ ...loginForm })
    auth.setAuth(res.access_token, res.user)
    ElMessage.success('登录成功')
    goHome(res.user)
  } catch { loadCaptcha() } finally { loading.value = false }
}

async function doRegister() {
  if (!regForm.username || !regForm.password) return ElMessage.warning('请填写完整信息')
  loading.value = true
  try {
    const res = await register({ ...regForm })
    ElMessage.success(res.message || '注册成功')
    tab.value = 'login'
    loginForm.username = regForm.username
    loadCaptcha()
  } catch {} finally { loading.value = false }
}

async function doForgot() {
  await forgotPassword({ ...forgotForm })
  ElMessage.success('密码已重置，请使用新密码登录')
  forgotVisible.value = false
  loginForm.username = forgotForm.username
}

onMounted(loadCaptcha)
</script>

<style scoped>
.login-wrap { min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #ffb56b 0%, #ff6d28 100%); }
.login-card { width: 400px; background: #fff; border-radius: 12px; padding: 32px; box-shadow: 0 8px 30px rgba(0,0,0,.15); }
.title { text-align: center; font-size: 26px; font-weight: 700; color: #ff6d28; margin-bottom: 20px; }
.captcha-row { display: flex; gap: 10px; width: 100%; }
.captcha-img { height: 40px; border-radius: 4px; cursor: pointer; }
.tips { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; }
</style>
