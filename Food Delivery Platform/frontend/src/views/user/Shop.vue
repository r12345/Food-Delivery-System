<template>
  <div class="shop-page" v-if="shop.id">
    <div class="shop-head">
      <img :src="shop.logo" class="logo" />
      <div class="head-info">
        <div class="name-row">
          <h2>{{ shop.name }}</h2>
          <el-button size="small" round :type="favorited ? 'warning' : 'default'" @click="toggleFav">
            {{ favorited ? '已收藏' : '收藏' }}
          </el-button>
        </div>
        <div class="meta">
          <el-rate :model-value="shop.rating" disabled size="small" />
          <span class="rating-num">{{ shop.rating }}</span>
          <span class="text-muted">月售{{ shop.sales }} · 起送¥{{ shop.min_price }} · 配送¥{{ shop.delivery_fee }} · {{ shop.business_hours }}</span>
        </div>
        <div class="text-muted">{{ shop.description }}（{{ shop.address }}）</div>
      </div>
    </div>

    <el-alert v-if="!shop.is_open" title="商家已打烊，暂不接受订单" type="warning" show-icon :closable="false" class="closed-tip" />

    <div class="menu-area">
      <div class="menu-cats">
        <div v-for="c in shop.menu" :key="c.id" class="menu-cat" :class="{ active: activeCat === c.id }"
             @click="activeCat = c.id">{{ c.name }}</div>
      </div>
      <div class="menu-foods">
        <template v-for="c in shop.menu" :key="c.id">
          <div v-show="activeCat === c.id">
            <div v-for="f in c.foods" :key="f.id" class="food-row">
              <img :src="f.image" class="food-img" @click="viewFood(f)" />
              <div class="food-mid">
                <div class="food-name" @click="viewFood(f)">{{ f.name }}</div>
                <div class="text-muted">月售{{ f.sales }} · 剩余{{ f.stock }}</div>
                <div class="price-row">
                  <span class="price">¥{{ f.price }}</span>
                  <span v-if="f.original_price > f.price" class="orig">¥{{ f.original_price }}</span>
                </div>
              </div>
              <div class="food-right">
                <template v-if="f.specs && f.specs.length">
                  <el-button type="primary" size="small" round @click="openSpec(f)">选规格</el-button>
                  <el-badge v-if="specCount(f)" :value="specCount(f)" class="spec-badge" />
                </template>
                <el-button v-else type="primary" size="small" circle @click="add(f)"><el-icon><Plus /></el-icon></el-button>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div class="cart-bar" v-if="myCart.length">
      <el-badge :value="totalQty" class="bar-badge">
        <div class="cart-icon"><el-icon :size="22"><ShoppingCart /></el-icon></div>
      </el-badge>
      <div class="bar-info">
        <div>¥{{ totalPrice.toFixed(2) }}</div>
        <div class="text-muted" v-if="shop.min_price > totalPrice">还差¥{{ (shop.min_price - totalPrice).toFixed(2) }}起送</div>
        <div class="text-muted" v-else>已达起送价</div>
      </div>
      <el-button type="primary" round :disabled="shop.min_price > totalPrice || !shop.is_open" @click="goCheckout">去结算</el-button>
    </div>

    <!-- 规格弹窗 -->
    <el-dialog v-model="specVisible" :title="specFood?.name" width="420px">
      <div v-for="(g, gi) in specFood?.specs || []" :key="gi" class="spec-group">
        <div class="spec-name">{{ g.name }}</div>
        <div class="spec-opts">
          <el-tag v-for="opt in g.options" :key="opt.name" size="large" class="spec-opt"
                  :type="selected[gi] === opt.name ? 'primary' : 'info'"
                  :effect="selected[gi] === opt.name ? 'dark' : 'plain'"
                  @click="selectSpec(gi, opt.name)">
            {{ opt.name }}<template v-if="opt.price">(+¥{{ opt.price }})</template>
          </el-tag>
        </div>
      </div>
      <template #footer>
        <div class="spec-footer">
          <span class="price">¥{{ specPrice.toFixed(2) }}</span>
          <el-button type="primary" @click="addSpec">加入购物车</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 菜品详情 -->
    <el-dialog v-model="foodVisible" :title="viewing?.name" width="460px">
      <img :src="viewing?.image" style="width:100%;border-radius:8px" />
      <p class="text-muted">{{ viewing?.description }}</p>
      <div>月售 {{ viewing?.sales }} · 库存 {{ viewing?.stock }}</div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, ShoppingCart } from '@element-plus/icons-vue'
import { useCart } from '../../stores/cart'
import { getShop, addCart, getFavoriteStatus, addFavorite, removeFavorite } from '../../api'

const route = useRoute()
const router = useRouter()
const cart = useCart()
const shop = ref({})
const activeCat = ref(0)
const favorited = ref(false)
const specVisible = ref(false)
const foodVisible = ref(false)
const specFood = ref(null)
const viewing = ref(null)
const selected = reactive({})
const specQty = ref(0)

const myCart = computed(() => {
  const g = cart.groups.find(g => g.shop_id === Number(route.params.id))
  return g ? g.items : []
})
const totalQty = computed(() => myCart.value.reduce((s, i) => s + i.quantity, 0))
const totalPrice = computed(() => myCart.value.reduce((s, i) => s + i.unit_price * i.quantity, 0))
const specPrice = computed(() => {
  if (!specFood.value) return 0
  let p = specFood.value.price
  specFood.value.specs.forEach((g, gi) => {
    const opt = g.options.find(o => o.name === selected[gi])
    if (opt) p += opt.price
  })
  return p
})

function specCount(f) {
  return myCart.value.filter(i => i.food_id === f.id && i.spec).reduce((s, i) => s + i.quantity, 0)
}

async function load() {
  shop.value = await getShop(route.params.id)
  activeCat.value = shop.value.menu[0]?.id || 0
  if (cart.count) await cart.refresh()
  if (localStorage.getItem('token')) {
    favorited.value = (await getFavoriteStatus(shop.value.id)).favorited
  }
}

async function toggleFav() {
  favorited.value = (await (favorited.value ? removeFavorite(shop.value.id) : addFavorite(shop.value.id))).favorited
  ElMessage.success(favorited.value ? '已收藏' : '已取消收藏')
}

async function add(f) {
  if (!shop.value.is_open) return ElMessage.warning('商家已打烊')
  const res = await addCart({ food_id: f.id, quantity: 1, spec: '' })
  cart.setCount(res.count)
  cart.refresh()
}

function openSpec(f) {
  specFood.value = f
  f.specs.forEach((g, gi) => { selected[gi] = selected[gi] && g.options.some(o => o.name === selected[gi]) ? selected[gi] : g.options[0]?.name })
  specQty.value = 0
  specVisible.value = true
}

function selectSpec(gi, name) { selected[gi] = name }

async function addSpec() {
  const specText = specFood.value.specs.map((g, gi) => selected[gi]).filter(Boolean).join('/')
  const res = await addCart({ food_id: specFood.value.id, quantity: 1, spec: specText })
  cart.setCount(res.count)
  cart.refresh()
  specVisible.value = false
  ElMessage.success('已加入购物车')
}

function viewFood(f) { viewing.value = f; foodVisible.value = true }
function goCheckout() { router.push('/checkout?shop_id=' + shop.value.id) }

onMounted(load)
</script>

<style scoped>
.shop-head { display: flex; gap: 16px; background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
.logo { width: 96px; height: 96px; border-radius: 10px; object-fit: cover; }
.head-info { flex: 1; }
.name-row { display: flex; align-items: center; justify-content: space-between; }
.name-row h2 { margin: 0 0 8px; }
.meta { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.rating-num { color: #ff9900; font-weight: 600; }
.closed-tip { margin-bottom: 16px; }
.menu-area { display: flex; background: #fff; border-radius: 12px; overflow: hidden; min-height: 420px; }
.menu-cats { width: 160px; background: #f8f8f8; }
.menu-cat { padding: 16px; cursor: pointer; font-size: 14px; border-left: 3px solid transparent; }
.menu-cat.active { background: #fff; border-left-color: #ff6d28; color: #ff6d28; font-weight: 600; }
.menu-foods { flex: 1; padding: 8px 16px; }
.food-row { display: flex; align-items: center; gap: 12px; padding: 14px 0; border-bottom: 1px dashed #f0f0f0; }
.food-img { width: 80px; height: 80px; border-radius: 8px; object-fit: cover; cursor: pointer; }
.food-mid { flex: 1; }
.food-name { font-weight: 600; margin-bottom: 4px; cursor: pointer; }
.price-row { display: flex; align-items: baseline; gap: 6px; margin-top: 4px; }
.price { color: #f56c6c; font-weight: 700; font-size: 17px; }
.orig { color: #c0c4cc; font-size: 12px; text-decoration: line-through; }
.food-right { position: relative; }
.spec-badge { position: absolute; top: -8px; right: -8px; }
.cart-bar { position: fixed; left: 50%; transform: translateX(-50%); bottom: 24px; width: 680px;
  background: #2b2f36; color: #fff; border-radius: 40px; display: flex; align-items: center;
  gap: 12px; padding: 10px 20px; z-index: 90; }
.cart-icon { width: 44px; height: 44px; border-radius: 50%; background: #ff6d28; display: flex; align-items: center; justify-content: center; }
.bar-info { flex: 1; }
.bar-info div:first-child { font-size: 18px; font-weight: 700; }
.bar-info .text-muted { color: #9ca3af !important; font-size: 12px; }
.spec-group { margin-bottom: 16px; }
.spec-name { font-weight: 600; margin-bottom: 8px; }
.spec-opts { display: flex; gap: 8px; flex-wrap: wrap; }
.spec-opt { cursor: pointer; }
.spec-footer { display: flex; justify-content: space-between; align-items: center; }
</style>
