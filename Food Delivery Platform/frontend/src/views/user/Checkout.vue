<template>
  <div class="checkout page-card">
    <h3>确认订单</h3>

    <div class="block">
      <div class="block-title">收货地址</div>
      <el-radio-group v-model="addressId" class="addr-list">
        <div v-for="a in addresses" :key="a.id" class="addr-item" :class="{ active: addressId === a.id }"
             @click="addressId = a.id">
          <div><b>{{ a.name }} {{ a.gender }}</b> {{ a.phone }} <el-tag v-if="a.is_default" size="small">默认</el-tag></div>
          <div class="text-muted">{{ a.region }} {{ a.detail }}</div>
        </div>
      </el-radio-group>
      <el-link type="primary" @click="$router.push('/address')">管理地址</el-link>
    </div>

    <div class="block">
      <div class="block-title">商品清单（{{ shopName }}）</div>
      <div v-for="it in items" :key="it.id" class="order-item">
        <img :src="it.image" class="oi-img" />
        <div class="oi-mid">{{ it.name }}<span class="text-muted" v-if="it.spec">（{{ it.spec }}）</span></div>
        <div class="oi-right">
          <span>x{{ it.quantity }}</span>
          <span class="price">¥{{ (it.unit_price * it.quantity).toFixed(2) }}</span>
        </div>
      </div>
    </div>

    <div class="block">
      <div class="block-title">优惠券</div>
      <el-select v-model="couponId" placeholder="选择优惠券" clearable style="max-width: 360px">
        <el-option v-for="c in usableCoupons" :key="c.uc_id"
                   :label="`${c.shop_name} ${c.name}（省¥${c.amount}）`" :value="c.uc_id" />
      </el-select>
      <div v-if="!usableCoupons.length" class="text-muted">暂无可用优惠券</div>
    </div>

    <div class="block">
      <div class="block-title">支付方式</div>
      <el-radio-group v-model="payType">
        <el-radio-button value="wechat">微信支付</el-radio-button>
        <el-radio-button value="alipay">支付宝</el-radio-button>
      </el-radio-group>
    </div>

    <div class="block">
      <div class="block-title">订单备注</div>
      <el-input v-model="remark" type="textarea" :rows="2" placeholder="口味偏好、放门口等" maxlength="100" />
    </div>

    <div class="summary">
      <div class="row"><span>商品合计</span><span>¥{{ total.toFixed(2) }}</span></div>
      <div class="row"><span>配送费</span><span>¥{{ deliveryFee.toFixed(2) }}</span></div>
      <div class="row" v-if="discount"><span>优惠券</span><span class="price">-¥{{ discount.toFixed(2) }}</span></div>
      <div class="row total"><span>待支付</span><span class="price">¥{{ payAmount.toFixed(2) }}</span></div>
      <el-button type="primary" size="large" style="width: 220px" :loading="submitting" @click="submit">提交订单</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useCart } from '../../stores/cart'
import { getAddresses, getMyCoupons, createOrder } from '../../api'

const route = useRoute()
const router = useRouter()
const cart = useCart()
const shopId = Number(route.query.shop_id)
const addresses = ref([])
const addressId = ref(null)
const couponId = ref(null)
const payType = ref('wechat')
const remark = ref('')
const coupons = ref([])
const submitting = ref(false)

const group = computed(() => cart.groups.find(g => g.shop_id === shopId))
const items = computed(() => group.value?.items || [])
const shopName = computed(() => group.value?.shop_name || '')
const deliveryFee = computed(() => group.value?.delivery_fee || 0)
const total = computed(() => items.value.reduce((s, i) => s + i.unit_price * i.quantity, 0))
const discount = computed(() => {
  const c = coupons.value.find(c => c.uc_id === couponId.value)
  return c && total.value >= c.threshold ? c.amount : 0
})
const payAmount = computed(() => Math.max(0, total.value + deliveryFee.value - discount.value))
const usableCoupons = computed(() =>
  coupons.value.filter(c => (c.shop_id === 0 || c.shop_id === shopId) && total.value >= c.threshold))

async function submit() {
  if (!addressId.value) return ElMessage.warning('请选择收货地址')
  submitting.value = true
  try {
    await createOrder({ address_id: addressId.value, shop_id: shopId, remark: remark.value,
                        pay_type: payType.value, coupon_id: couponId.value || 0 })
    ElMessage.success('下单成功，请尽快支付')
    cart.refresh()
    router.push('/orders')
  } catch {} finally { submitting.value = false }
}

onMounted(async () => {
  await cart.refresh()
  addresses.value = (await getAddresses()).list
  addressId.value = addresses.value.find(a => a.is_default)?.id || addresses.value[0]?.id
  coupons.value = (await getMyCoupons({ status: 'unused' })).list
  if (!items.value.length) {
    ElMessage.warning('购物车为空')
    router.replace('/')
  }
})
</script>

<style scoped>
.page-card { background: #fff; border-radius: 12px; padding: 24px; max-width: 760px; margin: 0 auto; }
.block { margin-bottom: 20px; }
.block-title { font-weight: 600; margin-bottom: 10px; }
.addr-list { display: block; width: 100%; }
.addr-item { border: 1px solid #eee; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; cursor: pointer; width: 100%; }
.addr-item.active { border-color: #ff6d28; background: #fff8f4; }
.order-item { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px dashed #f0f0f0; }
.oi-img { width: 52px; height: 52px; border-radius: 6px; object-fit: cover; }
.oi-mid { flex: 1; }
.oi-right { display: flex; gap: 16px; align-items: center; }
.summary { border-top: 1px solid #eee; padding-top: 16px; margin-top: 8px; display: flex; flex-direction: column; gap: 8px; align-items: flex-end; }
.summary .row { width: 240px; display: flex; justify-content: space-between; }
.summary .total { font-size: 18px; font-weight: 700; }
</style>
