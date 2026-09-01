<template>
  <div class="coupons">
    <el-card style="max-width: 520px">
      <template #header><b>创建店铺优惠券</b></template>
      <el-form :model="form" label-width="90px">
        <el-form-item label="券名称"><el-input v-model="form.name" placeholder="如：满25减5" /></el-form-item>
        <el-form-item label="使用门槛"><el-input-number v-model="form.threshold" :min="0" :precision="2" /></el-form-item>
        <el-form-item label="优惠金额"><el-input-number v-model="form.amount" :min="0.5" :precision="2" /></el-form-item>
        <el-form-item label="发放总量"><el-input-number v-model="form.total" :min="1" /></el-form-item>
        <el-form-item label="有效期">
          <el-date-picker v-model="range" type="datetimerange" value-format="YYYY-MM-DD HH:mm:ss"
                          start-placeholder="开始时间" end-placeholder="结束时间" style="width:100%" />
        </el-form-item>
        <el-button type="primary" @click="create">创建优惠券</el-button>
      </el-form>
    </el-card>

    <el-card style="flex:1">
      <template #header><b>我的优惠券</b></template>
      <el-table :data="list">
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column label="门槛/金额" width="130">
          <template #default="{ row }">满¥{{ row.threshold }} 减¥{{ row.amount }}</template>
        </el-table-column>
        <el-table-column label="领取" width="90">
          <template #default="{ row }">{{ row.received }}/{{ row.total }}</template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始" width="160" />
        <el-table-column prop="end_time" label="结束" width="160" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status ? 'success' : 'info'" size="small">{{ row.status ? '进行中' : '已停用' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { mGetCoupons, mAddCoupon } from '../../api'

const list = ref([])
const range = ref([])
const form = reactive({ name: '', threshold: 0, amount: 5, total: 100 })

async function create() {
  if (!form.name || !range.value?.length) return ElMessage.warning('请填写完整信息')
  await mAddCoupon({ ...form, start_time: range.value[0], end_time: range.value[1] })
  ElMessage.success('创建成功')
  form.name = ''
  load()
}

function load() { mGetCoupons().then(r => (list.value = r.list)) }
onMounted(load)
</script>

<style scoped>
.coupons { display: flex; gap: 16px; align-items: flex-start; }
</style>
