<template>
  <el-card>
    <div class="toolbar">
      <el-input v-model="kw" placeholder="订单号" clearable style="width:220px" @keyup.enter="load" />
      <el-select v-model="status" clearable placeholder="全部状态" style="width:150px" @change="load">
        <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
    </div>

    <el-table :data="list">
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="expand-box">
            <div v-for="it in row.items" :key="it.id" class="exp-item">
              <img :src="it.image" />
              <span>{{ it.food_name }}<i class="text-muted" v-if="it.spec">（{{ it.spec }}）</i> x{{ it.quantity }}</span>
              <span>¥{{ (it.price * it.quantity).toFixed(2) }}</span>
            </div>
            <div class="text-muted" style="margin-top:8px">
              收货：{{ row.address.name }} {{ row.address.phone }}（{{ row.address.region }} {{ row.address.detail }}）
              <template v-if="row.remark"> · 备注：{{ row.remark }}</template>
              <template v-if="row.cancel_reason"> · 原因：{{ row.cancel_reason }}</template>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="order_no" label="订单号" width="190" />
      <el-table-column prop="shop_name" label="商家" width="150" show-overflow-tooltip />
      <el-table-column prop="user_name" label="用户" width="100" />
      <el-table-column prop="pay_amount" label="实付" width="90">
        <template #default="{ row }"><span class="price">¥{{ row.pay_amount }}</span></template>
      </el-table-column>
      <el-table-column prop="pay_type" label="支付" width="80">
        <template #default="{ row }">{{ { wechat: '微信', alipay: '支付宝' }[row.pay_type] || '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type || 'info'" size="small">{{ statusMap[row.status]?.label || row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="下单时间" width="170" />
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <el-popconfirm v-if="row.status === 'refunding'" title="确定同意退款？" @confirm="agreeRefund(row)">
            <template #reference><el-link type="warning">同意退款</el-link></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination class="pager" layout="total, prev, pager, next" :total="total"
                   :page-size="query.size" v-model:current-page="query.page" @current-change="load" />
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { aGetOrders, aAgreeRefund, getDict } from '../../api'

const list = ref([])
const total = ref(0)
const statusOptions = ref([])
const kw = ref('')
const status = ref('')
const query = reactive({ keyword: '', status: '', page: 1, size: 10 })
const statusMap = {
  pending_pay: { label: '待付款', type: 'info' }, pending_accept: { label: '待接单', type: 'danger' },
  preparing: { label: '备餐中', type: 'warning' }, delivering: { label: '配送中', type: 'primary' },
  completed: { label: '已完成', type: 'success' }, cancelled: { label: '已取消', type: 'info' },
  refunding: { label: '退款中', type: 'warning' }, refunded: { label: '已退款', type: 'info' }
}

async function load() {
  Object.assign(query, { keyword: kw.value, status: status.value })
  const res = await aGetOrders(query)
  list.value = res.list
  total.value = res.total
}

async function agreeRefund(row) {
  await aAgreeRefund(row.id)
  ElMessage.success('退款成功')
  load()
}

onMounted(async () => {
  statusOptions.value = await getDict('order_status')
  load()
})
</script>

<style scoped>
.toolbar { display: flex; gap: 10px; margin-bottom: 14px; }
.pager { margin-top: 14px; justify-content: flex-end; }
.expand-box { padding: 8px 24px; }
.exp-item { display: flex; align-items: center; gap: 10px; padding: 4px 0; font-size: 14px; }
.exp-item img { width: 36px; height: 36px; border-radius: 4px; object-fit: cover; }
.exp-item span:first-of-type { flex: 1; }
</style>
