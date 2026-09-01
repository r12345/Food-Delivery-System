<template>
  <el-card style="max-width: 760px">
    <template #header>
      <div class="card-head"><b>管理员账号</b>
        <el-button size="small" type="primary" @click="dialogOpen = true">新增管理员</el-button>
      </div>
    </template>
    <el-table :data="list">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="用户名" width="140" />
      <el-table-column prop="nickname" label="昵称" width="140" />
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag type="success" size="small">{{ row.status ? '正常' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
    </el-table>
    <div class="text-muted" style="margin-top:12px">
      说明：管理员拥有全部后台权限（角色/菜单权限为简化版，统一为超管角色）
    </div>
  </el-card>

  <el-dialog v-model="dialogOpen" title="新增管理员" width="400px">
    <el-form :model="form" label-width="70px">
      <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
      <el-form-item label="昵称"><el-input v-model="form.nickname" /></el-form-item>
      <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password placeholder="至少6位" /></el-form-item>
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
import { aGetAdmins, aAddAdmin } from '../../api'

const list = ref([])
const dialogOpen = ref(false)
const form = reactive({ username: '', nickname: '', password: '' })

async function save() {
  if (!form.username || !form.password) return ElMessage.warning('请填写完整信息')
  await aAddAdmin({ ...form })
  ElMessage.success('添加成功')
  dialogOpen.value = false
  form.username = ''
  form.nickname = ''
  form.password = ''
  load()
}

function load() { aGetAdmins().then(r => (list.value = r.list)) }
onMounted(load)
</script>

<style scoped>
.card-head { display: flex; justify-content: space-between; align-items: center; }
</style>
