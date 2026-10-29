<template>
  <el-container class="merchant-layout">
    <el-aside width="200px" class="aside">
      <div class="brand">乐享外卖 · 商家端</div>
      <el-menu :default-active="$route.path" router background-color="#1f2d3d" text-color="#bfcbd9"
               active-text-color="#409eff" class="menu">
        <el-menu-item index="/merchant"><el-icon><Odometer /></el-icon>工作台</el-menu-item>
        <el-menu-item index="/merchant/shop"><el-icon><Shop /></el-icon>店铺管理</el-menu-item>
        <el-menu-item index="/merchant/foods"><el-icon><Food /></el-icon>菜品管理</el-menu-item>
        <el-menu-item index="/merchant/orders">
          <el-icon><List /></el-icon>订单处理
          <el-badge v-if="newOrders" :value="newOrders" class="badge" />
        </el-menu-item>
        <el-menu-item index="/merchant/finance"><el-icon><Money /></el-icon>财务管理</el-menu-item>
        <el-menu-item index="/merchant/reviews"><el-icon><ChatDotRound /></el-icon>评价管理</el-menu-item>
        <el-menu-item index="/merchant/coupons"><el-icon><Ticket /></el-icon>优惠券营销</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="left">
          <el-tag v-if="shop.status === 'approved'" :type="shop.is_open ? 'success' : 'info'" effect="dark">
            {{ shop.is_open ? '营业中' : '已打烊' }}
          </el-tag>
          <el-tag v-else type="warning">店铺审核中/未通过</el-tag>
          <span class="shop-name">{{ shop.name || '未入驻店铺' }}</span>
        </div>
        <div class="right">
          <el-switch v-if="shop.status === 'approved'" v-model="openState" active-text="营业"
                     inactive-text="打烊" @change="toggleOpen" style="margin-right: 16px" />
          <el-dropdown @command="cmd => cmd === 'logout' && doLogout()">
            <span class="admin-name">{{ auth.user?.nickname }}<el-icon><ArrowDown /></el-icon></span>
            <template #dropdown>
              <el-dropdown-menu><el-dropdown-item command="logout">退出登录</el-dropdown-item></el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="content"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElNotification } from 'element-plus'
import { Odometer, Shop, Food, List, Money, ChatDotRound, Ticket, ArrowDown } from '@element-plus/icons-vue'
import { useAuth } from '../stores/auth'
import bus from '../utils/bus'
import { mGetShop, mSetOpen } from '../api'

const router = useRouter()
const auth = useAuth()
const shop = ref({})
const newOrders = ref(0)
let ws = null
let reconnectTimer = null
let closedByUs = false
let retry = 0

const openState = computed({
  get: () => !!shop.value.is_open,
  set: () => {}
})

async function loadShop() {
  try { shop.value = await mGetShop() } catch { /* 未入驻 */ }
}

async function toggleOpen(v) {
  shop.value = await mSetOpen(v)
}

function doLogout() {
  closedByUs = true
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  if (ws) { ws.onclose = null; ws.close(); ws = null }
  auth.logout()
  router.push('/login')
}

function connectWS() {
  if (auth.role !== 'merchant') return
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return
  closedByUs = false
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  ws = new WebSocket(`${proto}://${location.host}/ws/merchant?token=${auth.token}`)
  ws.onopen = () => { retry = 0 }
  ws.onmessage = e => {
    const d = JSON.parse(e.data)
    if (d.type === 'new_order') {
      newOrders.value++
      ElNotification({ title: '新订单提醒', message: `订单 ${d.order_no}，实付 ¥${d.pay_amount}，请及时接单`, type: 'success', duration: 0 })
      bus.emit('merchant-new-order', d)
    }
  }
  ws.onclose = () => {
    ws = null
    // 修正：组件卸载 / 主动登出后不再重连，避免形成重连循环；重连间隔按退避递增
    if (closedByUs) return
    retry = Math.min(retry + 1, 6)
    const delay = Math.min(3000 * retry, 30000)
    reconnectTimer = setTimeout(connectWS, delay)
  }
  ws.onerror = () => { /* 交由 onclose 统一处理重连 */ }
}

watch(() => router.currentRoute.value.path, p => { if (p === '/merchant/orders') newOrders.value = 0 })

onMounted(() => { loadShop(); connectWS() })
onUnmounted(() => {
  closedByUs = true
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  if (ws) { ws.onclose = null; ws.close(); ws = null }
})

</script>

<style scoped>
.merchant-layout { height: 100vh; }
.aside { background: #1f2d3d; }
.brand { color: #fff; font-weight: 700; font-size: 16px; padding: 20px 16px; border-bottom: 1px solid rgba(255,255,255,.08); }
.menu { border-right: none; }
.badge { margin-left: 8px; }
.header { background: #fff; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 1px 4px rgba(0,0,0,.06); }
.left { display: flex; align-items: center; gap: 12px; }
.shop-name { font-weight: 600; }
.admin-name { cursor: pointer; display: flex; align-items: center; gap: 4px; }
.content { background: #f5f6fa; overflow: auto; }
</style>
