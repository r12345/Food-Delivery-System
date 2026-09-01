<template>
  <div class="orders">
    <el-tabs v-model="tab" @tab-change="load">
      <el-tab-pane v-for="t in tabs" :key="t.value" :label="t.label" :name="t.value" />
    </el-tabs>

    <div v-for="o in orders" :key="o.id" class="order-card">
      <div class="oc-head">
        <div>
          <b>{{ o.shop_name }}</b>
          <span class="text-muted" style="margin-left:12px">{{ o.created_at }}</span>
        </div>
        <el-tag :type="statusMap[o.status]?.type || 'info'" effect="light">{{ statusMap[o.status]?.label || o.status }}</el-tag>
      </div>
      <div class="oc-body" @click="detailVisible(o)">
        <div class="oc-items">
          <div v-for="it in o.items.slice(0, 3)" :key="it.id" class="oc-item">
            <img :src="it.image" />
            <span>{{ it.name }}<i v-if="it.spec" class="text-muted">（{{ it.spec }}）</i> x{{ it.quantity }}</span>
          </div>
          <span v-if="o.items.length > 3" class="text-muted">等{{ o.items.length }}件商品</span>
        </div>
        <div class="oc-amount">¥{{ o.pay_amount.toFixed(2) }}</div>
      </div>
      <div class="oc-foot">
        <span class="text-muted">{{ o.address.name }} {{ o.address.phone }} · {{ o.address.detail }}</span>
        <div class="actions">
          <el-button v-if="o.status === 'pending_pay'" type="primary" size="small" @click="openPay(o)">去支付</el-button>
          <el-button v-if="['pending_pay', 'pending_accept'].includes(o.status)" size="small" @click="doCancel(o)">取消订单</el-button>
          <el-button v-if="o.status === 'delivering'" type="success" size="small" @click="doConfirm(o)">确认收货</el-button>
          <el-button v-if="['pending_accept', 'preparing', 'delivering'].includes(o.status)" type="warning" size="small" plain @click="doRefund(o)">申请退款</el-button>
          <el-button v-if="o.status === 'completed' && !o.has_evaluation" type="primary" plain size="small" @click="openEval(o)">去评价</el-button>
        </div>
      </div>
    </div>
    <el-empty v-if="!orders.length" description="暂无订单" />

    <!-- 订单详情 -->
    <el-dialog v-model="detailOpen" title="订单详情" width="520px">
      <template v-if="current">
        <div class="d-row"><span class="text-muted">订单号</span>{{ current.order_no }}</div>
        <div class="d-row"><span class="text-muted">状态</span>{{ statusMap[current.status]?.label }}</div>
        <div class="d-row"><span class="text-muted">收货</span>{{ current.address.name }} {{ current.address.phone }}（{{ current.address.region }} {{ current.address.detail }}）</div>
        <div class="d-row"><span class="text-muted">配送费</span>¥{{ current.delivery_fee }}</div>
        <div class="d-row" v-if="current.discount_amount"><span class="text-muted">优惠</span>-¥{{ current.discount_amount }}</div>
        <div class="d-row" v-if="current.remark"><span class="text-muted">备注</span>{{ current.remark }}</div>
        <div v-for="it in current.items" :key="it.id" class="d-item">
          <span>{{ it.food_name }} <i class="text-muted" v-if="it.spec">{{ it.spec }}</i> x{{ it.quantity }}</span>
          <span>¥{{ (it.price * it.quantity).toFixed(2) }}</span>
        </div>
      </template>
    </el-dialog>

    <!-- 支付弹窗（模拟） -->
    <el-dialog v-model="payOpen" title="订单支付（模拟）" width="380px">
      <div v-if="current" class="pay-amount">¥{{ current.pay_amount.toFixed(2) }}</div>
      <el-radio-group v-model="payType" size="large" class="pay-types">
        <el-radio-button value="wechat">微信支付</el-radio-button>
        <el-radio-button value="alipay">支付宝</el-radio-button>
      </el-radio-group>
      <template #footer>
        <el-button @click="payOpen = false">取消</el-button>
        <el-button type="success" @click="doPay">确认支付</el-button>
      </template>
    </el-dialog>

    <!-- 评价弹窗 -->
    <el-dialog v-model="evalOpen" title="评价订单" width="440px">
      <el-form label-width="90px">
        <el-form-item label="商家评分"><el-rate v-model="evalForm.shop_rating" allow-half /></el-form-item>
        <el-form-item label="骑手评分"><el-rate v-model="evalForm.rider_rating" allow-half /></el-form-item>
        <el-form-item label="评价内容">
          <el-input v-model="evalForm.content" type="textarea" :rows="3" placeholder="味道怎么样？服务如何？" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="evalOpen = false">取消</el-button>
        <el-button type="primary" @click="doEval">提交评价</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMyOrders, payOrder, cancelOrder, confirmOrder, refundOrder, createEvaluation, getDict } from '../../api'

const tabs = [
  { label: '全部', value: '' }, { label: '待付款', value: 'pending_pay' },
  { label: '待接单', value: 'pending_accept' }, { label: '备餐中', value: 'preparing' },
  { label: '配送中', value: 'delivering' }, { label: '已完成', value: 'completed' },
  { label: '退款/售后', value: 'refunding' }
]
const tab = ref('')
const orders = ref([])
const statusMap = ref({})
const current = ref(null)
const detailOpen = ref(false)
const payOpen = ref(false)
const evalOpen = ref(false)
const payType = ref('wechat')
const evalForm = ref({ shop_rating: 5, rider_rating: 5, content: '' })

async function load() {
  const res = await getMyOrders({ status: tab.value, page: 1, size: 50 })
  orders.value = res.list
}

function detailVisible(o) { current.value = o; detailOpen.value = true }
function openPay(o) { current.value = o; payType.value = 'wechat'; payOpen.value = true }
function openEval(o) { current.value = o; evalForm.value = { shop_rating: 5, rider_rating: 5, content: '' }; evalOpen.value = true }

async function doPay() {
  const res = await payOrder(current.value.id, payType.value)
  ElMessage.success('支付成功，等待商家接单')
  payOpen.value = false
  load()
}

async function doCancel(o) {
  await ElMessageBox.confirm('确定取消该订单吗？', '提示', { type: 'warning' })
  await cancelOrder(o.id)
  ElMessage.success('订单已取消')
  load()
}

async function doConfirm(o) {
  await confirmOrder(o.id)
  ElMessage.success('订单已完成')
  load()
}

async function doRefund(o) {
  await ElMessageBox.confirm('确定申请退款吗？需商家或平台审核', '提示', { type: 'warning' })
  await refundOrder(o.id)
  ElMessage.success('退款申请已提交')
  load()
}

async function doEval() {
  await createEvaluation(current.value.id, { ...evalForm.value })
  ElMessage.success('评价成功，感谢反馈')
  evalOpen.value = false
  load()
}

onMounted(async () => {
  statusMap.value = Object.fromEntries((await getDict('order_status')).map(i => [i.value, i]))
  await load()
})
</script>

<style scoped>
.orders { max-width: 760px; margin: 0 auto; }
.order-card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
.oc-head { display: flex; justify-content: space-between; margin-bottom: 10px; }
.oc-body { display: flex; align-items: center; cursor: pointer; padding: 8px 0; }
.oc-items { flex: 1; }
.oc-item { display: flex; align-items: center; gap: 8px; padding: 3px 0; font-size: 14px; }
.oc-item img { width: 36px; height: 36px; border-radius: 4px; object-fit: cover; }
.oc-amount { font-weight: 700; color: #303133; }
.oc-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; }
.actions { display: flex; gap: 8px; }
.d-row { display: flex; gap: 12px; margin-bottom: 8px; font-size: 14px; }
.d-row .text-muted { width: 48px; flex-shrink: 0; }
.d-item { display: flex; justify-content: space-between; padding: 6px 0; border-top: 1px dashed #f0f0f0; font-size: 14px; }
.pay-amount { text-align: center; font-size: 32px; font-weight: 700; color: #f56c6c; margin-bottom: 16px; }
.pay-types { display: flex; justify-content: center; }
</style>
