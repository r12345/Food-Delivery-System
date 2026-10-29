<template>
  <div class="marketing">
    <el-card>
      <template #header>
        <div class="card-head"><b>首页轮播广告位</b>
          <el-button size="small" type="primary" @click="bannerOpen = true">新增广告</el-button>
        </div>
      </template>
      <el-table :data="banners">
        <el-table-column label="图片" width="160">
          <template #default="{ row }"><img :src="row.image" class="banner-img" /></template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="160" />
        <el-table-column prop="sort" label="排序" width="80" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status ? 'success' : 'info'" size="small">{{ row.status ? '展示中' : '已下架' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-popconfirm title="确定删除该广告？" @confirm="delBanner(row)">
              <template #reference><el-link type="danger">删除</el-link></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-head"><b>平台优惠券</b>
          <el-button size="small" type="primary" @click="couponOpen = true">发平台券</el-button>
        </div>
      </template>
      <el-table :data="coupons">
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column label="门槛/金额" width="130">
          <template #default="{ row }">满¥{{ row.threshold }} 减¥{{ row.amount }}</template>
        </el-table-column>
        <el-table-column label="领取" width="90">
          <template #default="{ row }">{{ row.received }}/{{ row.total }}</template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始" width="160" />
        <el-table-column prop="end_time" label="结束" width="160" />
      </el-table>
    </el-card>

    <el-dialog v-model="bannerOpen" title="新增轮播广告" width="460px">
      <el-form :model="bForm" label-width="80px">
        <el-form-item label="标题"><el-input v-model="bForm.title" /></el-form-item>
        <el-form-item label="图片">
          <el-upload :action="'/api/upload'" name="file" :headers="upHeaders" :show-file-list="false"
                     :on-success="res => (bForm.image = res.url)" accept="image/*">
            <img v-if="bForm.image" :src="bForm.image" class="up-img" />
            <el-button v-else>上传图片</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="跳转链接"><el-input v-model="bForm.link" placeholder="可空" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="bForm.sort" :min="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bannerOpen = false">取消</el-button>
        <el-button type="primary" @click="saveBanner">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="couponOpen" title="发放平台优惠券" width="440px">
      <el-form :model="cForm" label-width="90px">
        <el-form-item label="券名称"><el-input v-model="cForm.name" /></el-form-item>
        <el-form-item label="使用门槛"><el-input-number v-model="cForm.threshold" :min="0" :precision="2" /></el-form-item>
        <el-form-item label="优惠金额"><el-input-number v-model="cForm.amount" :min="0.5" :precision="2" /></el-form-item>
        <el-form-item label="发放总量"><el-input-number v-model="cForm.total" :min="1" /></el-form-item>
        <el-form-item label="有效期">
          <el-date-picker v-model="range" type="datetimerange" value-format="YYYY-MM-DD HH:mm:ss"
                          start-placeholder="开始" end-placeholder="结束" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="couponOpen = false">取消</el-button>
        <el-button type="primary" @click="saveCoupon">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuth } from '../../stores/auth'
import { aGetBanners, aAddBanner, aDeleteBanner, aGetPlatformCoupons, aAddPlatformCoupon } from '../../api'

const auth = useAuth()
// 修正：用 computed 保持响应式，token 刷新后上传请求不会携带过期令牌
const upHeaders = computed(() => ({ Authorization: 'Bearer ' + auth.token }))
const banners = ref([])
const coupons = ref([])
const bannerOpen = ref(false)
const couponOpen = ref(false)
const range = ref([])
const bForm = reactive({ title: '', image: '', link: '', sort: 0 })
const cForm = reactive({ name: '', threshold: 0, amount: 8, total: 100 })

async function saveBanner() {
  if (!bForm.image) return ElMessage.warning('请上传广告图片')
  await aAddBanner({ ...bForm })
  ElMessage.success('已添加')
  bannerOpen.value = false
  bForm.title = ''
  bForm.image = ''
  load()
}

async function delBanner(row) {
  await aDeleteBanner(row.id)
  ElMessage.success('已删除')
  load()
}

async function saveCoupon() {
  if (!cForm.name || !range.value?.length) return ElMessage.warning('请填写完整信息')
  await aAddPlatformCoupon({ ...cForm, start_time: range.value[0], end_time: range.value[1] })
  ElMessage.success('发放成功')
  couponOpen.value = false
  load()
}

function load() {
  aGetBanners().then(r => (banners.value = r.list))
  aGetPlatformCoupons().then(r => (coupons.value = r.list))
}

onMounted(load)
</script>

<style scoped>
.card-head { display: flex; justify-content: space-between; align-items: center; }
.banner-img { width: 130px; height: 50px; border-radius: 6px; object-fit: cover; }
.up-img { width: 200px; height: 80px; border-radius: 8px; object-fit: cover; }
</style>
