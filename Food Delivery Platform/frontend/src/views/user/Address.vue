<template>
  <div class="address-page">
    <div class="head">
      <h3>收货地址</h3>
      <el-button type="primary" @click="openDialog()">新增地址</el-button>
    </div>

    <div class="addr-grid">
      <div v-for="a in list" :key="a.id" class="addr-card" :class="{ default: a.is_default }">
        <div class="addr-line"><b>{{ a.name }} {{ a.gender }}</b><span>{{ a.phone }}</span>
          <el-tag v-if="a.is_default" size="small" type="success">默认</el-tag></div>
        <div class="text-muted">{{ a.region }} {{ a.detail }}</div>
        <div class="addr-ops">
          <el-link v-if="!a.is_default" type="primary" @click="setDefault(a)">设为默认</el-link>
          <el-link type="primary" @click="openDialog(a)">编辑</el-link>
          <el-link type="danger" @click="del(a)">删除</el-link>
        </div>
      </div>
      <el-empty v-if="!list.length" description="还没有收货地址" style="grid-column:1/-1" />
    </div>

    <el-dialog v-model="dialogOpen" :title="form.id ? '编辑地址' : '新增地址'" width="480px">
      <el-form :model="form" label-width="70px">
        <el-form-item label="联系人"><el-input v-model="form.name" placeholder="姓名" /></el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio value="先生">先生</el-radio>
            <el-radio value="女士">女士</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="所在地区">
          <el-cascader v-model="regionArr" :options="regions" :props="{ value: 'name', label: 'name' }"
                       style="width:100%" placeholder="省 / 市 / 区" />
        </el-form-item>
        <el-form-item label="详细地址"><el-input v-model="form.detail" placeholder="街道、楼牌号等" /></el-form-item>
        <el-form-item label="设为默认"><el-switch v-model="form.is_default" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogOpen = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAddresses, addAddress, updateAddress, deleteAddress, getRegions } from '../../api'

const list = ref([])
const regions = ref([])
const dialogOpen = ref(false)
const regionArr = ref([])
const form = reactive({ id: 0, name: '', phone: '', gender: '先生', detail: '', is_default: false })

function openDialog(a) {
  Object.assign(form, a ? { ...a } : { id: 0, name: '', phone: '', gender: '先生', detail: '', is_default: false })
  regionArr.value = a?.region ? a.region.split(' ').filter(Boolean) : []
  dialogOpen.value = true
}

async function load() { list.value = (await getAddresses()).list }

async function save() {
  if (!form.name || !form.phone || !form.detail) return ElMessage.warning('请填写完整地址信息')
  const region = regionArr.value.join(' ')
  const data = { name: form.name, phone: form.phone, gender: form.gender,
                 region, detail: form.detail, is_default: form.is_default }
  if (form.id) await updateAddress(form.id, data)
  else await addAddress(data)
  ElMessage.success('保存成功')
  dialogOpen.value = false
  load()
}

async function setDefault(a) {
  await updateAddress(a.id, { ...a, is_default: true })
  load()
}

async function del(a) {
  await ElMessageBox.confirm('确定删除该地址吗？', '提示', { type: 'warning' })
  await deleteAddress(a.id)
  ElMessage.success('已删除')
  load()
}

onMounted(async () => {
  load()
  regions.value = await getRegions()
})
</script>

<style scoped>
.address-page { max-width: 860px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 24px; }
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.head h3 { margin: 0; }
.addr-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.addr-card { border: 1px solid #eee; border-radius: 10px; padding: 14px; }
.addr-card.default { border-color: #ff6d28; background: #fffaf6; }
.addr-line { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.addr-line span { color: #909399; }
.addr-ops { display: flex; gap: 16px; margin-top: 10px; }
</style>
