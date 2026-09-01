<template>
  <el-card>
    <div class="toolbar">
      <el-tabs v-model="status" style="flex:1" @tab-change="load">
        <el-tab-pane label="待审核" name="pending" />
        <el-tab-pane label="已通过" name="approved" />
        <el-tab-pane label="已驳回" name="rejected" />
        <el-tab-pane label="已封禁" name="banned" />
        <el-tab-pane label="全部" name="" />
      </el-tabs>
      <el-input v-model="kw" placeholder="店铺名称" clearable style="width:180px" @keyup.enter="load" />
    </div>
    <el-table :data="list">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="店铺" min-width="200">
        <template #default="{ row }">
          <div style="display:flex;align-items:center;gap:10px">
            <img :src="row.logo" class="shop-logo" />
            <div>
              <div><b>{{ row.name }}</b></div>
              <div class="text-muted">{{ row.address }}</div>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="owner_name" label="账号" width="110" />
      <el-table-column prop="category_name" label="分类" width="100" />
      <el-table-column prop="phone" label="电话" width="120" />
      <el-table-column prop="rating" label="评分" width="70" />
      <el-table-column prop="sales" label="销量" width="80" />
      <el-table-column prop="created_at" label="申请时间" width="170" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusTag[row.status]?.type" size="small">{{ statusTag[row.status]?.label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-link type="success" @click="audit(row, 'approved')">通过</el-link>
            <el-link type="danger" style="margin-left:8px" @click="audit(row, 'rejected')">驳回</el-link>
          </template>
          <el-link v-else-if="row.status === 'approved'" type="danger" @click="audit(row, 'banned')">封禁</el-link>
          <el-link v-else-if="row.status === 'banned'" type="success" @click="audit(row, 'approved')">解封</el-link>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination class="pager" layout="total, prev, pager, next" :total="total"
                   :page-size="10" v-model:current-page="page" @current-change="load" />
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { aGetShops, aAuditShop } from '../../api'

const list = ref([])
const total = ref(0)
const status = ref('pending')
const kw = ref('')
const page = ref(1)
const statusTag = {
  pending: { label: '待审核', type: 'warning' }, approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' }, banned: { label: '已封禁', type: 'danger' }
}

async function load() {
  const res = await aGetShops({ status: status.value, keyword: kw.value, page: page.value, size: 10 })
  list.value = res.list
  total.value = res.total
}

async function audit(row, action) {
  if (action === 'rejected') {
    await ElMessageBox.confirm(`确定驳回「${row.name}」的入驻申请？`, '提示', { type: 'warning' })
  }
  await aAuditShop(row.id, action)
  ElMessage.success('操作成功')
  load()
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; }
.shop-logo { width: 44px; height: 44px; border-radius: 6px; object-fit: cover; }
.pager { margin-top: 14px; justify-content: flex-end; }
</style>
