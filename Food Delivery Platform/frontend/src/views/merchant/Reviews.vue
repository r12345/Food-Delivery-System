<template>
  <el-card>
    <el-table :data="list">
      <el-table-column prop="order_no" label="订单号" width="190" />
      <el-table-column prop="nickname" label="用户" width="110" />
      <el-table-column label="商家评分" width="150">
        <template #default="{ row }"><el-rate :model-value="row.shop_rating" disabled size="small" /></template>
      </el-table-column>
      <el-table-column label="骑手评分" width="150">
        <template #default="{ row }"><el-rate :model-value="row.rider_rating" disabled size="small" /></template>
      </el-table-column>
      <el-table-column prop="content" label="评价内容" min-width="180" show-overflow-tooltip />
      <el-table-column label="回复" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">{{ row.reply || '-' }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="160" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-link type="primary" @click="openReply(row)">{{ row.reply ? '修改回复' : '回复' }}</el-link>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="replyOpen" title="回复评价" width="440px">
    <div v-if="current" class="text-muted" style="margin-bottom:8px">
      {{ current.nickname }}：{{ current.content }}
    </div>
    <el-input v-model="replyText" type="textarea" :rows="3" placeholder="感谢您的评价..." />
    <template #footer>
      <el-button @click="replyOpen = false">取消</el-button>
      <el-button type="primary" @click="doReply">提交回复</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { mGetEvaluations, mReplyEvaluation } from '../../api'

const list = ref([])
const replyOpen = ref(false)
const replyText = ref('')
const current = ref(null)

function openReply(row) {
  current.value = row
  replyText.value = row.reply || ''
  replyOpen.value = true
}

async function doReply() {
  if (!replyText.value.trim()) return ElMessage.warning('请输入回复内容')
  await mReplyEvaluation(current.value.id, replyText.value)
  ElMessage.success('回复成功')
  replyOpen.value = false
  load()
}

function load() { mGetEvaluations({ page: 1, size: 50 }).then(r => (list.value = r.list)) }
onMounted(load)
</script>
