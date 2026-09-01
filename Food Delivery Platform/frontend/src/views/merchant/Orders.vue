<template>
  <div class="m-orders">
    <el-tabs v-model="tab" @tab-change="load">
      <el-tab-pane :label="`待接单(${counts.pending_accept})`" name="pending_accept" />
      <el-tab-pane label="备餐中" name="preparing" />
      <el-tab-pane label="配送中" name="delivering" />
      <el-tab-pane label="退款/售后" name="refunding" />
      <el-tab-pane label="已完成" name="completed" />
      <el-tab-pane label="全部" name="" />
    </el-tabs>

    <div v-for="o in orders" :key="o.id" class="o-card">
      <div class="o-head">
        <div>
          <b>{{ o.order_no }}</b>
          <span class="text-muted" style="margin-left:10px">{{ o.created_at }} · {{ o.user_name }}</span>
        </div>
        <el-tag :type="statusMap[o.status]?.type || 'info'">{{ statusMap[o.status]?.label || o.status }}</el-tag>
      </div>
      <div class="o-body">
        <div v-for="it in o.items" :key="it.id" class="o-item">
          <img :src="it.image" />
          <span>{{ it.food_name }}<i class="text-muted" v-if="it.spec">（{{ it.spec }}）</i> x{{ it.quantity }}</span>
          <span class="price">¥{{ (it.price * it.quantity).toFixed(2) }}</span>
        </div>
        <div class="o-info text-muted">
          配送费 ¥{{ o.delivery_fee }}
          <template v-if="o.discount_amount"> · 优惠 -¥{{ o.discount_amount }}</template>
          <template v-if="o.remark"> · 备注：<b style="color:#e6a23c">{{ o.remark }}</b></template>
        </div>
      </div>
      <div class="o-foot">
        <div class="text-muted">{{ o.address.name }} {{ o.address.phone }}（{{ o.address.region }} {{ o.address.detail }}）</div>
        <div class="o-amount">实付 <span class="price">¥{{ o.pay_amount.toFixed(2) }}</span></div>
        <div class="o-actions">
          <el-button v-if="o.status === 'pending_accept'" type="primary" size="small" @click="act(mAcceptOrder, o)">接单</el-button>
          <el-button v-if="o.status === 'pending_accept'" type="danger" plain size="small" @click="reject(o)">拒单</el-button>
          <el-button v-if="o.status === 'preparing'" type="warning" size="small" @click="act(mDeliverOrder, o)">出餐配送</el-button>
          <el-button v-if="o.status === 'refunding'" type="warning" size="small" @click="agreeRefund(o)">同意退款</el-button>
          <el-button size="small" @click="print(o)">打印</el-button>
          <el-button size="small" text @click="showDetail(o)">详情</el-button>
        </div>
      </div>
    </div>
    <el-empty v-if="!orders.length" description="暂无订单" />

    <el-dialog v-model="detailOpen" title="订单详情" width="520px">
      <template v-if="current">
        <div class="d-row"><span class="text-muted">订单号</span>{{ current.order_no }}</div>
        <div class="d-row"><span class="text-muted">下单时间</span>{{ current.created_at }}</div>
        <div class="d-row"><span class="text-muted">支付方式</span>{{ current.pay_type === 'wechat' ? '微信支付' : current.pay_type === 'alipay' ? '支付宝' : '未支付' }}</div>
        <div class="d-row"><span class="text-muted">支付时间</span>{{ current.pay_time || '-' }}</div>
        <div class="d-row"><span class="text-muted">收货</span>{{ current.address.name }} {{ current.address.phone }}（{{ current.address.region }} {{ current.address.detail }}）</div>
        <div class="d-row" v-if="current.cancel_reason"><span class="text-muted">取消/退款原因</span>{{ current.cancel_reason }}</div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import bus from '../../utils/bus'
import { mGetOrders, mAcceptOrder, mRejectOrder, mDeliverOrder, mAgreeRefund } from '../../api'

const tab = ref('pending_accept')
const orders = ref([])
const counts = reactive({ pending_accept: 0 })
const current = ref(null)
const detailOpen = ref(false)
const statusMap = {
  pending_pay: { label: '待付款', type: 'info' }, pending_accept: { label: '待接单', type: 'danger' },
  preparing: { label: '备餐中', type: 'warning' }, delivering: { label: '配送中', type: 'primary' },
  completed: { label: '已完成', type: 'success' }, cancelled: { label: '已取消', type: 'info' },
  refunding: { label: '退款中', type: 'warning' }, refunded: { label: '已退款', type: 'info' }
}

async function load() {
  const res = await mGetOrders({ status: tab.value, page: 1, size: 50 })
  orders.value = res.list
  const all = tab.value === 'pending_accept' ? res.total : (await mGetOrders({ status: 'pending_accept', page: 1, size: 1 })).total
  counts.pending_accept = all
}

async function act(fn, o) {
  await fn(o.id)
  ElMessage.success('操作成功')
  load()
}

async function reject(o) {
  const { value } = await ElMessageBox.prompt('请输入拒单原因', '拒单', { inputValue: '商家已售罄' })
  await mRejectOrder(o.id, value)
  ElMessage.success('已拒单，款项将退回用户')
  load()
}

async function agreeRefund(o) {
  await ElMessageBox.confirm(`确定同意退款 ¥${o.pay_amount}？`, '提示', { type: 'warning' })
  await mAgreeRefund(o.id)
  ElMessage.success('退款成功')
  load()
}

function showDetail(o) { current.value = o; detailOpen.value = true }

function print(o) {
  const rows = o.items.map(i => `<tr><td>${i.food_name}${i.spec ? '(' + i.spec + ')' : ''}</td><td>x${i.quantity}</td><td>¥${(i.price * i.quantity).toFixed(2)}</td></tr>`).join('')
  const w = window.open('', '_blank', 'width=420,height=600')
  w.document.write(`
    <h2 style="text-align:center">后厨小票</h2>
    <p>订单号：${o.order_no}<br/>时间：${o.created_at}<br/>收货：${o.address.name} ${o.address.phone}<br/>地址：${o.address.region} ${o.address.detail}</p>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
      <tr><th>菜品</th><th>数量</th><th>金额</th></tr>${rows}
    </table>
    <p>配送费：¥${o.delivery_fee} ${o.discount_amount ? '优惠：-¥' + o.discount_amount : ''}<br/>
    <b>实付：¥${o.pay_amount}</b></p>
    ${o.remark ? '<p style="color:red">备注：' + o.remark + '</p>' : ''}`)
  w.document.close()
  w.print()
}

onMounted(() => { load(); bus.on('merchant-new-order', load) })
onUnmounted(() => bus.off('merchant-new-order', load))
</script>

<style scoped>
.o-card { background: #fff; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; }
.o-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.o-item { display: flex; align-items: center; gap: 10px; padding: 4px 0; font-size: 14px; }
.o-item img { width: 40px; height: 40px; border-radius: 4px; object-fit: cover; }
.o-item span:first-of-type { flex: 1; }
.o-info { margin-top: 6px; font-size: 13px; }
.o-foot { display: flex; align-items: center; gap: 16px; margin-top: 10px; border-top: 1px dashed #eee; padding-top: 10px; }
.o-foot .text-muted { flex: 1; }
.o-amount { font-weight: 600; }
.d-row { display: flex; gap: 12px; margin-bottom: 8px; font-size: 14px; }
.d-row .text-muted { width: 90px; flex-shrink: 0; }
</style>
