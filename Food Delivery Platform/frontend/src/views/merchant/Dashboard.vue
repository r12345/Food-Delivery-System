<template>
  <div>
    <div class="stat-row">
      <el-card v-for="s in stats" :key="s.label" class="stat-card" shadow="hover">
        <div class="stat-value">{{ s.value }}</div>
        <div class="text-muted">{{ s.label }}</div>
      </el-card>
    </div>

    <el-card>
      <template #header>
        <div class="card-head"><b>最新订单</b>
          <el-link type="primary" @click="$router.push('/merchant/orders')">查看全部</el-link>
        </div>
      </template>
      <el-table :data="recent" size="large">
        <el-table-column prop="order_no" label="订单号" width="200" />
        <el-table-column label="菜品">
          <template #default="{ row }">
            {{ row.items.map(i => i.food_name + 'x' + i.quantity).join('，') }}
          </template>
        </el-table-column>
        <el-table-column prop="pay_amount" label="实付" width="100">
          <template #default="{ row }"><span class="price">¥{{ row.pay_amount }}</span></template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }"><el-tag size="small">{{ statusLabel(row.status) }}</el-tag></template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { mGetDashboard } from '../../api'

const dashboard = ref({})
const summary = computed(() => dashboard.value.summary || {})
const recent = computed(() => dashboard.value.recent_orders || [])
const stats = computed(() => [
  { label: '今日营业额', value: '¥' + (summary.value.today_amount || 0) },
  { label: '今日订单', value: summary.value.today_orders || 0 },
  { label: '待接单', value: summary.value.pending_orders || 0 },
  { label: '本月营业额', value: '¥' + (summary.value.month_amount || 0) },
  { label: '累计收入', value: '¥' + (summary.value.total_income || 0) }
])
const statusLabelMap = {
  pending_pay: '待付款', pending_accept: '待接单', preparing: '备餐中', delivering: '配送中',
  completed: '已完成', cancelled: '已取消', refunding: '退款中', refunded: '已退款'
}
const statusLabel = s => statusLabelMap[s] || s

onMounted(async () => { dashboard.value = await mGetDashboard() })
</script>

<style scoped>
.stat-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { text-align: center; }
.stat-value { font-size: 24px; font-weight: 700; color: #ff6d28; }
.card-head { display: flex; justify-content: space-between; align-items: center; }
</style>
