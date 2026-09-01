<template>
  <div class="user-layout">
    <header class="topbar">
      <div class="topbar-inner page">
        <a class="logo" @click="$router.push('/')">
          <span class="logo-icon">乐享外卖</span>
          <span class="logo-sub">让美味更快到达</span>
        </a>
        <el-input v-model="kw" class="search" placeholder="搜索商家、菜品" clearable @keyup.enter="doSearch">
          <template #append>
            <el-button @click="doSearch">搜索</el-button>
          </template>
        </el-input>
        <div class="right">
          <el-badge :value="unread" :hidden="!unread" class="bell">
            <el-icon :size="20" @click="showNotice"><Bell /></el-icon>
          </el-badge>
          <el-badge :value="cart.count" :hidden="!cart.count">
            <el-icon :size="20" @click="cartVisible = true"><ShoppingCart /></el-icon>
          </el-badge>
          <el-dropdown v-if="auth.isLogged" @command="onCommand">
            <span class="user-name">{{ auth.user?.nickname || auth.user?.username }}<el-icon><ArrowDown /></el-icon></span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="orders">我的订单</el-dropdown-item>
                <el-dropdown-item command="address">收货地址</el-dropdown-item>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button v-else type="primary" @click="$router.push('/login')">登录</el-button>
        </div>
      </div>
    </header>

    <main class="main page">
      <router-view />
    </main>

    <el-drawer v-model="cartVisible" title="我的购物车" size="420px">
      <div v-if="!cart.groups.length" class="empty">购物车是空的，快去逛逛吧</div>
      <div v-for="g in cart.groups" :key="g.shop_id" class="cart-group">
        <div class="group-head">
          <b>{{ g.shop_name }}</b>
          <el-button link type="primary" @click="$router.push('/checkout?shop_id=' + g.shop_id); cartVisible = false">去结算</el-button>
        </div>
        <div v-for="it in g.items" :key="it.id" class="cart-item">
          <img :src="it.image" class="ci-img" />
          <div class="ci-mid">
            <div class="ci-name">{{ it.name }}</div>
            <div class="text-muted">{{ it.spec }}</div>
          </div>
          <div class="ci-right">
            <div class="price">¥{{ it.unit_price }}</div>
            <div class="qty">
              <el-button size="small" circle @click="changeQty(it, it.quantity - 1)"><el-icon><Minus /></el-icon></el-button>
              <span>{{ it.quantity }}</span>
              <el-button size="small" circle @click="changeQty(it, it.quantity + 1)"><el-icon><Plus /></el-icon></el-button>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { Bell, ShoppingCart, ArrowDown, Minus, Plus } from '@element-plus/icons-vue'
import { useAuth } from '../stores/auth'
import { useCart } from '../stores/cart'
import { updateCart, removeCart, getNotifications, readNotifications } from '../api'

const router = useRouter()
const auth = useAuth()
const cart = useCart()
const kw = ref('')
const cartVisible = ref(false)
const unread = ref(0)

function doSearch() {
  router.push({ path: '/', query: { kw: kw.value } })
}

function onCommand(cmd) {
  if (cmd === 'logout') {
    auth.logout()
    cart.setCount(0)
    router.push('/login')
  } else {
    router.push('/' + cmd)
  }
}

async function changeQty(item, qty) {
  try {
    if (qty <= 0) {
      await removeCart(item.id)
    } else {
      await updateCart(item.id, qty)
    }
    cart.refresh()
  } catch { /* 已在拦截器提示 */ }
}

async function showNotice() {
  const res = await getNotifications()
  unread.value = res.unread
  if (!res.list.length) return ElMessage.info('暂无消息')
  await readNotifications()
  unread.value = 0
  const html = res.list.slice(0, 8).map(n => `
    <div style="text-align:left;margin-bottom:10px">
      <b>${n.title}</b><div style="color:#909399;font-size:12px">${n.created_at}</div>
      <div style="font-size:13px">${n.content}</div>
    </div>`).join('')
  ElMessageBox.alert(html, '消息通知', { dangerouslyUseHTMLString: true, confirmButtonText: '知道了' })
}

onMounted(() => {
  if (auth.isLogged && auth.role === 'user') {
    cart.refresh()
    getNotifications().then(res => (unread.value = res.unread)).catch(() => {})
  }
})
</script>

<style scoped>
.topbar { background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,.06); position: sticky; top: 0; z-index: 100; }
.topbar-inner { display: flex; align-items: center; gap: 24px; height: 64px; }
.logo { cursor: pointer; white-space: nowrap; }
.logo-icon { font-size: 22px; font-weight: 700; color: #ff6d28; }
.logo-sub { font-size: 12px; color: #909399; margin-left: 8px; }
.search { max-width: 420px; flex: 1; }
.right { display: flex; align-items: center; gap: 20px; margin-left: auto; }
.bell { cursor: pointer; }
.user-name { cursor: pointer; display: flex; align-items: center; gap: 4px; }
.main { min-height: calc(100vh - 64px); }
.cart-group { margin-bottom: 16px; border: 1px solid #eee; border-radius: 8px; padding: 12px; }
.group-head { display: flex; justify-content: space-between; margin-bottom: 8px; }
.cart-item { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px dashed #f0f0f0; }
.ci-img { width: 56px; height: 56px; border-radius: 6px; object-fit: cover; }
.ci-mid { flex: 1; }
.ci-name { font-size: 14px; }
.ci-right { text-align: right; }
.qty { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.empty { text-align: center; color: #909399; padding: 60px 0; }
</style>
