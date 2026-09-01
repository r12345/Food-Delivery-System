<template>
  <div class="profile">
    <div class="p-card">
      <div class="head">
        <h3>个人中心</h3>
      </div>
      <div class="info-row">
        <el-upload :action="'/api/upload'" name="file" :headers="upHeaders" :show-file-list="false"
                   :on-success="onAvatar" accept="image/*">
          <el-avatar :size="72" :src="form.avatar">{{ form.nickname?.[0] || 'U' }}</el-avatar>
        </el-upload>
        <el-form :model="form" label-width="60px" style="flex:1; max-width: 420px">
          <el-form-item label="昵称"><el-input v-model="form.nickname" /></el-form-item>
          <el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item>
          <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
          <el-button type="primary" @click="save">保存资料</el-button>
        </el-form>
      </div>
    </div>

    <el-tabs v-model="tab" class="p-tabs">
      <el-tab-pane label="我的收藏" name="fav">
        <div class="fav-grid">
          <div v-for="s in favorites" :key="s.id" class="fav-card" @click="$router.push('/shop/' + s.id)">
            <img :src="s.logo" />
            <div>
              <div class="fav-name">{{ s.name }}</div>
              <div class="text-muted">评分{{ s.rating }} · 月售{{ s.sales }}</div>
            </div>
            <el-button size="small" text type="danger" @click.stop="unfav(s)">取消收藏</el-button>
          </div>
          <el-empty v-if="!favorites.length" description="暂无收藏" style="grid-column:1/-1" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="我的优惠券" name="coupon">
        <el-tabs v-model="cpTab">
          <el-tab-pane label="未使用" name="unused" />
          <el-tab-pane label="已使用/过期" name="used" />
        </el-tabs>
        <div class="coupon-grid">
          <div v-for="c in shownCoupons" :key="c.uc_id" class="coupon" :class="{ used: c.uc_status === 'used' || c.expired }">
            <div class="cp-amount"><b>¥{{ c.amount }}</b><span>满{{ c.threshold }}可用</span></div>
            <div class="cp-info">
              <div class="cp-name">{{ c.name }}</div>
              <div class="text-muted">{{ c.shop_name }} · {{ c.end_time }} 到期</div>
            </div>
          </div>
          <el-empty v-if="!shownCoupons.length" description="暂无优惠券" style="grid-column:1/-1" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="我的评价" name="eval">
        <div v-for="e in evals" :key="e.id" class="eval-card">
          <div class="eval-head">
            <b>{{ e.shop_name }}</b>
            <el-rate :model-value="e.shop_rating" disabled size="small" />
            <span class="text-muted">{{ e.created_at }}</span>
          </div>
          <div>{{ e.content }}</div>
          <div v-if="e.reply" class="reply"><b>商家回复：</b>{{ e.reply }}</div>
        </div>
        <el-empty v-if="!evals.length" description="暂无评价" />
      </el-tab-pane>

      <el-tab-pane label="领优惠券" name="receive">
        <div class="coupon-grid">
          <div v-for="c in receivable" :key="c.id" class="coupon">
            <div class="cp-amount"><b>¥{{ c.amount }}</b><span>满{{ c.threshold }}可用</span></div>
            <div class="cp-info">
              <div class="cp-name">{{ c.name }}</div>
              <div class="text-muted">{{ c.shop_name }} · 剩余{{ c.total - c.received }}张</div>
            </div>
            <el-button type="primary" size="small" round :disabled="c.received_by_me" @click="receive(c)">
              {{ c.received_by_me ? '已领取' : '领取' }}
            </el-button>
          </div>
          <el-empty v-if="!receivable.length" description="暂无可领取的优惠券" style="grid-column:1/-1" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuth } from '../../stores/auth'
import { getMe, updateMe, getFavorites, removeFavorite, getMyCoupons, getMyEvaluations, getReceivableCoupons, receiveCoupon } from '../../api'

const auth = useAuth()
const tab = ref('fav')
const cpTab = ref('unused')
const form = reactive({ nickname: '', phone: '', email: '', avatar: '' })
const favorites = ref([])
const myCoupons = ref([])
const evals = ref([])
const receivable = ref([])
const upHeaders = { Authorization: 'Bearer ' + auth.token }

const shownCoupons = computed(() =>
  cpTab.value === 'unused'
    ? myCoupons.value.filter(c => c.uc_status === 'unused' && !c.expired)
    : myCoupons.value.filter(c => c.uc_status === 'used' || c.expired))

function onAvatar(res) {
  form.avatar = res.url
  ElMessage.success('头像已上传，点击保存资料生效')
}

async function save() {
  const u = await updateMe({ ...form })
  auth.setUser({ ...auth.user, ...u })
  ElMessage.success('资料已更新')
}

async function unfav(s) {
  await removeFavorite(s.id)
  favorites.value = favorites.value.filter(f => f.id !== s.id)
}

async function receive(c) {
  await receiveCoupon(c.id)
  ElMessage.success('领取成功')
  loadCoupons()
}

onMounted(async () => {
  Object.assign(form, await getMe())
  favorites.value = (await getFavorites()).list
  myCoupons.value = (await getMyCoupons()).list
  evals.value = (await getMyEvaluations()).list
  receivable.value = (await getReceivableCoupons()).list
})
</script>

<style scoped>
.profile { max-width: 900px; margin: 0 auto; }
.p-card { background: #fff; border-radius: 12px; padding: 24px; margin-bottom: 16px; }
.head h3 { margin: 0 0 16px; }
.info-row { display: flex; gap: 28px; align-items: flex-start; }
.p-tabs { background: #fff; border-radius: 12px; padding: 16px 24px 24px; }
.fav-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.fav-card { display: flex; align-items: center; gap: 12px; border: 1px solid #eee; border-radius: 10px; padding: 12px; cursor: pointer; }
.fav-card img { width: 64px; height: 64px; border-radius: 8px; object-fit: cover; }
.fav-name { font-weight: 600; margin-bottom: 4px; }
.fav-card > div:nth-child(2) { flex: 1; }
.coupon-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 8px; }
.coupon { display: flex; border: 1px solid #ffe0c2; border-radius: 10px; overflow: hidden; align-items: center; }
.coupon.used { opacity: .5; filter: grayscale(.6); }
.cp-amount { background: #fff3ec; color: #ff6d28; padding: 14px 16px; text-align: center; display: flex; flex-direction: column; min-width: 90px; }
.cp-amount b { font-size: 20px; }
.cp-amount span { font-size: 11px; }
.cp-info { flex: 1; padding: 10px 14px; }
.cp-name { font-weight: 600; margin-bottom: 4px; }
.coupon .el-button { margin-right: 12px; }
.eval-card { border-bottom: 1px dashed #f0f0f0; padding: 12px 0; }
.eval-head { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.reply { background: #f7f8fa; border-radius: 8px; padding: 8px 12px; margin-top: 8px; font-size: 13px; }
</style>
