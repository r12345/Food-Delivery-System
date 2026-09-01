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
        <div class="card-head"><b>流水记录</b>
          <el-button size="small" type="primary" @click="withdrawVisible = true">提现申请</el-button>
        </div>
      </template>
      <el-table :data="records">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="类型" width="110">
          <template #default="{ row }">
            <el-tag :type="typeMap[row.type]?.t" size="small">{{ typeMap[row.type]?.l }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="120">
          <template #default="{ row }">
            <span :class="row.amount >= 0 ? 'price' : 'income-pos'">¥{{ row.amount.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="140" />
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>
    </el-card>

    <el-dialog v-model="withdrawVisible" title="提现申请" width="380px">
      <div class="text-muted" style="margin-bottom:10px">可提现余额：¥{{ (summary.balance || 0).toFixed(2) }}</div>
      <el-input-number v-model="withdrawAmount" :min="0.01" :max="summary.balance || 0" :precision="2" style="width:100%" />
      <template #footer>
        <el-button @click="withdrawVisible = false">取消</el-button>
        <el-button type="primary" @click="doWithdraw">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { mFinanceSummary, mFinanceRecords, mWithdraw } from '../../api'

const summary = ref({})
const records = ref([])
const withdrawVisible = ref(false)
const withdrawAmount = ref(0)

const stats = computed(() => [
  { label: '今日营业额', value: '¥' + (summary.value.today_amount || 0) },
  { label: '本月营业额', value: '¥' + (summary.value.month_amount || 0) },
  { label: '累计收入', value: '¥' + (summary.value.total_income || 0) },
  { label: '已提现', value: '¥' + Math.abs(summary.value.withdraw_amount || 0) },
  { label: '可提现余额', value: '¥' + (summary.value.balance || 0) }
])
const typeMap = {
  order_income: { l: '订单收入', t: 'success' }, refund: { l: '退款', t: 'danger' },
  withdraw: { l: '提现', t: 'warning' }
}

async function doWithdraw() {
  await mWithdraw(withdrawAmount.value)
  ElMessage.success('提现申请已提交，等待平台打款')
  withdrawVisible.value = false
  load()
}

function load() {
  mFinanceSummary().then(s => (summary.value = s))
  mFinanceRecords({ page: 1, size: 30 }).then(r => (records.value = r.list))
}

onMounted(load)
</script>

<style scoped>
.stat-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { text-align: center; }
.stat-value { font-size: 22px; font-weight: 700; color: #ff6d28; }
.card-head { display: flex; justify-content: space-between; align-items: center; }
.income-pos { color: #67c23a; font-weight: 600; }
</style>
