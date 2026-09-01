<template>
  <el-card>
    <div class="toolbar">
      <el-input v-model="kw" placeholder="姓名/手机号" clearable style="width:200px" @keyup.enter="load" />
      <el-button type="primary" @click="load">查询</el-button>
      <el-button type="success" style="margin-left:auto" @click="dialogOpen = true">新增骑手</el-button>
    </div>
    <el-table :data="list">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="phone" label="手机号" width="140" />
      <el-table-column prop="orders_count" label="完成单量" width="100" />
      <el-table-column prop="income" label="累计收入" width="110">
        <template #default="{ row }">¥{{ row.income }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status ? 'success' : 'info'" size="small">{{ row.status ? '接单中' : '已停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="入职时间" width="170" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-popconfirm :title="`确定${row.status ? '停用' : '启用'}？`" @confirm="toggle(row)">
            <template #reference>
              <el-link :type="row.status ? 'danger' : 'success'">{{ row.status ? '停用' : '启用' }}</el-link>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="dialogOpen" title="新增骑手" width="380px">
    <el-form :model="form" label-width="70px">
      <el-form-item label="姓名"><el-input v-model="form.name" /></el-form-item>
      <el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogOpen = false">取消</el-button>
      <el-button type="primary" @click="save">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { aGetRiders, aAddRider, aSetRiderStatus } from '../../api'

const list = ref([])
const kw = ref('')
const dialogOpen = ref(false)
const form = reactive({ name: '', phone: '' })

async function load() {
  list.value = (await aGetRiders({ keyword: kw.value, page: 1, size: 50 })).list
}

async function toggle(row) {
  await aSetRiderStatus(row.id, row.status ? 0 : 1)
  load()
}

async function save() {
  if (!form.name) return ElMessage.warning('请填写姓名')
  await aAddRider({ ...form })
  ElMessage.success('添加成功')
  dialogOpen.value = false
  form.name = ''
  form.phone = ''
  load()
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 10px; margin-bottom: 14px; }
</style>
