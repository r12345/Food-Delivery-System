<template>
  <el-card>
    <div class="toolbar">
      <el-input v-model="query.keyword" placeholder="用户名/昵称/手机号" clearable style="width:220px" @keyup.enter="load" />
      <el-select v-model="query.role" clearable placeholder="角色" style="width:140px" @change="load">
        <el-option label="普通用户" value="user" />
        <el-option label="商家" value="merchant" />
        <el-option label="管理员" value="admin" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
    </div>
    <el-table :data="list">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="nickname" label="昵称" width="120" />
      <el-table-column prop="phone" label="手机号" width="130" />
      <el-table-column label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="{ user: '', merchant: 'warning', admin: 'danger' }[row.role]" size="small">
            {{ { user: '用户', merchant: '商家', admin: '管理员' }[row.role] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="注册时间" width="170" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status ? 'success' : 'danger'" size="small">{{ row.status ? '正常' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <el-popconfirm :title="`确定${row.status ? '禁用' : '启用'}该账号？`" @confirm="toggle(row)">
            <template #reference>
              <el-link :type="row.status ? 'danger' : 'success'">{{ row.status ? '禁用' : '启用' }}</el-link>
            </template>
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
import { aGetUsers, aSetUserStatus } from '../../api'

const list = ref([])
const total = ref(0)
const query = reactive({ keyword: '', role: '', page: 1, size: 10 })

async function load() {
  const res = await aGetUsers(query)
  list.value = res.list
  total.value = res.total
}

async function toggle(row) {
  await aSetUserStatus(row.id, row.status ? 0 : 1)
  load()
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 10px; margin-bottom: 14px; }
.pager { margin-top: 14px; justify-content: flex-end; }
</style>
