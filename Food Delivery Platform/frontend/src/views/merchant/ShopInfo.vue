<template>
  <el-card v-if="shop.id" style="max-width: 720px">
    <template #header>
      <div class="card-head">
        <b>店铺信息</b>
        <el-tag :type="statusTag[shop.status]?.type" effect="dark">{{ statusTag[shop.status]?.label }}</el-tag>
      </div>
    </template>

    <el-alert v-if="shop.status === 'pending'" title="店铺正在等待平台审核，审核通过后可营业"
              type="warning" show-icon :closable="false" style="margin-bottom:16px" />
    <el-alert v-if="shop.status === 'rejected'" title="入驻申请被驳回，请联系平台或修改资料后重新提交"
              type="error" show-icon :closable="false" style="margin-bottom:16px" />
    <el-alert v-if="shop.status === 'banned'" title="店铺已被平台封禁"
              type="error" show-icon :closable="false" style="margin-bottom:16px" />

    <el-form :model="form" label-width="90px">
      <el-form-item label="店铺LOGO">
        <el-upload :action="'/api/upload'" name="file" :headers="upHeaders" :show-file-list="false"
                   :on-success="res => (form.logo = res.url)" accept="image/*">
          <img v-if="form.logo" :src="form.logo" class="up-logo" />
          <el-button v-else>上传LOGO</el-button>
        </el-upload>
      </el-form-item>
      <el-form-item label="门头图">
        <el-upload :action="'/api/upload'" name="file" :headers="upHeaders" :show-file-list="false"
                   :on-success="res => (form.cover = res.url)" accept="image/*">
          <img v-if="form.cover" :src="form.cover" class="up-cover" />
          <el-button v-else>上传门头图</el-button>
        </el-upload>
      </el-form-item>
      <el-form-item label="店铺名称"><el-input v-model="form.name" /></el-form-item>
      <el-form-item label="店铺简介"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
      <el-form-item label="联系电话"><el-input v-model="form.phone" /></el-form-item>
      <el-form-item label="店铺地址"><el-input v-model="form.address" /></el-form-item>
      <el-form-item label="营业时间"><el-input v-model="form.business_hours" placeholder="09:00-21:00" /></el-form-item>
      <el-form-item label="起送价(¥)"><el-input-number v-model="form.min_price" :min="0" /></el-form-item>
      <el-form-item label="配送费(¥)"><el-input-number v-model="form.delivery_fee" :min="0" /></el-form-item>
      <el-form-item label="配送范围"><el-input-number v-model="form.delivery_range" :min="1" :max="20" /> <span style="margin-left:8px">公里</span></el-form-item>
      <el-button type="primary" :loading="saving" @click="save">保存修改</el-button>
    </el-form>
  </el-card>
  <el-empty v-else description="店铺不存在" />
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuth } from '../../stores/auth'
import { mGetShop, mUpdateShop } from '../../api'

const auth = useAuth()
const shop = ref({})
const form = reactive({})
const saving = ref(false)
const upHeaders = { Authorization: 'Bearer ' + auth.token }
const statusTag = {
  pending: { label: '待审核', type: 'warning' }, approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' }, banned: { label: '已封禁', type: 'danger' }
}

async function save() {
  saving.value = true
  try {
    shop.value = await mUpdateShop({ ...form })
    ElMessage.success('保存成功')
  } finally { saving.value = false }
}

onMounted(async () => {
  shop.value = await mGetShop()
  Object.assign(form, shop.value)
})
</script>

<style scoped>
.card-head { display: flex; justify-content: space-between; align-items: center; }
.up-logo { width: 80px; height: 80px; border-radius: 8px; object-fit: cover; cursor: pointer; }
.up-cover { width: 200px; height: 100px; border-radius: 8px; object-fit: cover; cursor: pointer; }
</style>
