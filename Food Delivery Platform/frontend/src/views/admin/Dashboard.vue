<template>
  <div>
    <div class="stat-row">
      <el-card v-for="s in stats" :key="s.label" class="stat-card" shadow="hover">
        <div class="stat-value">{{ s.value }}</div>
        <div class="text-muted">{{ s.label }}</div>
      </el-card>
    </div>

    <div class="chart-row">
      <el-card class="chart-card">
        <template #header><b>近7天营业额 / 订单量趋势</b></template>
        <div ref="trendRef" class="chart" />
      </el-card>
      <el-card class="chart-card">
        <template #header><b>订单状态分布</b></template>
        <div ref="pieRef" class="chart" />
      </el-card>
    </div>

    <el-card style="margin-top:16px">
      <template #header><b>热门商家 TOP5（按销量）</b></template>
      <div ref="hotRef" class="chart hot" />
    </el-card>
  </div>
</template>

<script setup>
import * as echarts from 'echarts'
import { computed, onMounted, ref } from 'vue'
import { aStatsOverview, aStatsTrend, aStatsHotShops, aStatsStatus } from '../../api'

const overview = ref({})
const trendRef = ref()
const pieRef = ref()
const hotRef = ref()

const stats = computed(() => [
  { label: '平台总营业额', value: '¥' + (overview.value.total_income || 0) },
  { label: '总订单量', value: overview.value.total_orders || 0 },
  { label: '今日营业额', value: '¥' + (overview.value.today_income || 0) },
  { label: '今日订单', value: overview.value.today_orders || 0 },
  { label: '注册用户', value: overview.value.user_count || 0 },
  { label: '入驻商家', value: overview.value.merchant_count || 0 },
  { label: '待审核商家', value: overview.value.pending_merchants || 0 },
  { label: '今日新增用户', value: overview.value.today_users || 0 }
])

function renderTrend(list) {
  echarts.init(trendRef.value).setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['营业额', '订单量'] },
    grid: { left: 50, right: 50, bottom: 30, top: 40 },
    xAxis: { type: 'category', data: list.map(i => i.date) },
    yAxis: [
      { type: 'value', name: '营业额(¥)' },
      { type: 'value', name: '订单量' }
    ],
    series: [
      { name: '营业额', type: 'line', smooth: true, data: list.map(i => i.amount),
        areaStyle: { opacity: 0.15 }, itemStyle: { color: '#ff6d28' } },
      { name: '订单量', type: 'bar', yAxisIndex: 1, data: list.map(i => i.orders),
        itemStyle: { color: '#409eff', opacity: 0.7 }, barWidth: 18 }
    ]
  })
}

function renderPie(list) {
  echarts.init(pieRef.value).setOption({
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', right: 10, top: 'center', type: 'scroll' },
    series: [{
      type: 'pie', radius: ['40%', '70%'], center: ['40%', '50%'],
      label: { show: false },
      data: list.map(i => ({ name: i.label, value: i.count }))
    }]
  })
}

function renderHot(list) {
  echarts.init(hotRef.value).setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 130, right: 40, top: 10, bottom: 30 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: list.map(i => i.name).reverse() },
    series: [{ type: 'bar', data: list.map(i => i.sales).reverse(),
      itemStyle: { color: '#ff9f43' }, barWidth: 18, label: { show: true, position: 'right' } }]
  })
}

onMounted(async () => {
  overview.value = await aStatsOverview()
  renderTrend((await aStatsTrend()).list)
  renderPie((await aStatsStatus()).list)
  renderHot((await aStatsHotShops()).list)
  window.addEventListener('resize', () => {
    [trendRef, pieRef, hotRef].forEach(r => echarts.getInstanceByDom(r.value)?.resize())
  })
})
</script>

<style scoped>
.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { text-align: center; }
.stat-value { font-size: 24px; font-weight: 700; color: #ff6d28; }
.chart-row { display: grid; grid-template-columns: 3fr 2fr; gap: 16px; }
.chart { height: 320px; }
.chart.hot { height: 260px; }
</style>
