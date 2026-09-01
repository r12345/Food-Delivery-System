<template>
  <div class="home">
    <el-carousel height="300px" class="banner" motion-blur>
      <el-carousel-item v-for="b in home.banners" :key="b.id">
        <img :src="b.image" class="banner-img" />
        <div class="banner-title">{{ b.title }}</div>
      </el-carousel-item>
    </el-carousel>

    <div class="cats">
      <div v-for="c in home.categories" :key="c.id" class="cat-item" :class="{ active: categoryId === c.id }"
           @click="toggleCat(c.id)">
        <img :src="c.icon" class="cat-icon" />
        <span>{{ c.name }}</span>
      </div>
    </div>

    <div class="section-head">
      <h3>{{ categoryId || kw ? '筛选结果' : '热门商家' }}</h3>
      <el-radio-group v-model="sort" size="small" @change="loadShops">
        <el-radio-button value="sales">销量</el-radio-button>
        <el-radio-button value="rating">评分</el-radio-button>
        <el-radio-button value="delivery_fee">配送费</el-radio-button>
      </el-radio-group>
    </div>

    <div class="shop-grid">
      <div v-for="s in shops" :key="s.id" class="shop-card" @click="$router.push('/shop/' + s.id)">
        <img :src="s.logo" class="shop-logo" />
        <div class="shop-info">
          <div class="shop-name">{{ s.name }}</div>
          <div class="shop-meta">
            <el-rate :model-value="s.rating" disabled size="small" />
            <span class="rating-num">{{ s.rating }}</span>
            <span class="text-muted">月售{{ s.sales }}</span>
          </div>
          <div class="shop-tags">
            <el-tag size="small" type="warning" effect="plain">起送 ¥{{ s.min_price }}</el-tag>
            <el-tag size="small" type="success" effect="plain">配送 ¥{{ s.delivery_fee }}</el-tag>
            <el-tag size="small" effect="plain">{{ s.business_hours }}</el-tag>
          </div>
          <div class="shop-desc text-muted">{{ s.description }}</div>
        </div>
      </div>
      <el-empty v-if="!shops.length" description="没有找到相关商家" style="grid-column: 1/-1" />
    </div>

    <div class="section-head"><h3>推荐美食</h3></div>
    <div class="food-grid">
      <div v-for="f in home.recommend_foods" :key="f.id" class="food-card" @click="$router.push('/shop/' + f.shop_id)">
        <img :src="f.image" class="food-img" />
        <div class="food-info">
          <div class="food-name">{{ f.name }}</div>
          <div class="text-muted">{{ f.shop_name }} · 月售{{ f.sales }}</div>
          <div class="food-price">¥{{ f.price }}<span v-if="f.original_price > f.price" class="orig">¥{{ f.original_price }}</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getHome, getShops } from '../../api'

const route = useRoute()
const home = reactive({ banners: [], categories: [], hot_shops: [], recommend_foods: [] })
const shops = ref([])
const categoryId = ref(0)
const sort = ref('sales')
const kw = ref(route.query.kw || '')

async function loadHome() {
  Object.assign(home, await getHome())
}

async function loadShops() {
  const res = await getShops({ keyword: kw.value, category_id: categoryId.value, sort: sort.value, page: 1, size: 20 })
  shops.value = res.list
}

function toggleCat(id) {
  categoryId.value = categoryId.value === id ? 0 : id
  loadShops()
}

watch(() => route.query.kw, v => {
  kw.value = v || ''
  loadShops()
})

onMounted(() => { loadHome(); loadShops() })
</script>

<style scoped>
.banner { border-radius: 12px; overflow: hidden; margin-bottom: 16px; }
.banner-img { width: 100%; height: 100%; object-fit: cover; }
.banner-title { position: absolute; left: 24px; bottom: 24px; color: #fff; font-size: 22px; font-weight: 700; text-shadow: 0 2px 8px rgba(0,0,0,.5); }
.cats { display: flex; gap: 20px; background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 16px; justify-content: space-around; }
.cat-item { display: flex; flex-direction: column; align-items: center; gap: 6px; cursor: pointer; font-size: 13px; padding: 4px 12px; border-radius: 8px; }
.cat-item.active { color: #ff6d28; background: #fff3ec; }
.cat-icon { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; }
.section-head { display: flex; justify-content: space-between; align-items: center; margin: 20px 0 12px; }
.section-head h3 { margin: 0; }
.shop-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.shop-card { display: flex; gap: 12px; background: #fff; border-radius: 12px; padding: 14px; cursor: pointer; transition: box-shadow .2s; }
.shop-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.1); }
.shop-logo { width: 88px; height: 88px; border-radius: 8px; object-fit: cover; flex-shrink: 0; }
.shop-info { flex: 1; min-width: 0; }
.shop-name { font-weight: 600; font-size: 16px; margin-bottom: 4px; }
.shop-meta { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.rating-num { color: #ff9900; font-weight: 600; font-size: 13px; }
.shop-tags { display: flex; gap: 6px; margin-bottom: 6px; flex-wrap: wrap; }
.shop-desc { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.food-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.food-card { background: #fff; border-radius: 12px; overflow: hidden; cursor: pointer; transition: box-shadow .2s; }
.food-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.1); }
.food-img { width: 100%; height: 140px; object-fit: cover; display: block; }
.food-info { padding: 10px 12px; }
.food-name { font-weight: 600; margin-bottom: 4px; }
.food-price { color: #f56c6c; font-weight: 700; margin-top: 6px; }
.orig { color: #c0c4cc; font-size: 12px; text-decoration: line-through; margin-left: 6px; font-weight: 400; }
</style>
