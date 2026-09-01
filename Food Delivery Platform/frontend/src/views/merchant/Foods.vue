<template>
  <div class="foods-page">
    <el-card class="cat-card" shadow="never">
      <template #header>
        <div class="card-head"><b>菜品分类</b>
          <el-button size="small" type="primary" @click="catDialog = true; catForm = { name: '', sort: 0 }">新增分类</el-button>
        </div>
      </template>
      <div v-for="c in categories" :key="c.id" class="cat-row">
        <span>{{ c.name }}</span>
        <span class="cat-ops">
          <el-link @click="editCat(c)">编辑</el-link>
          <el-link type="danger" @click="delCat(c)">删除</el-link>
        </span>
      </div>
    </el-card>

    <el-card class="food-card" shadow="never">
      <template #header>
        <div class="card-head">
          <div style="display:flex;gap:12px;align-items:center">
            <b>菜品列表</b>
            <el-select v-model="query.category_id" clearable placeholder="全部分类" style="width:140px" @change="load">
              <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-input v-model="query.keyword" placeholder="搜索菜品" clearable style="width:180px" @keyup.enter="load" />
          </div>
          <el-button size="small" type="primary" @click="openFood()">新增菜品</el-button>
        </div>
      </template>
      <el-table :data="foods">
        <el-table-column label="图片" width="80">
          <template #default="{ row }"><img :src="row.image" class="tbl-img" /></template>
        </el-table-column>
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column label="分类" width="110">
          <template #default="{ row }">{{ catName(row.category_id) }}</template>
        </el-table-column>
        <el-table-column prop="price" label="价格" width="90">
          <template #default="{ row }"><span class="price">¥{{ row.price }}</span></template>
        </el-table-column>
        <el-table-column prop="original_price" label="原价" width="90" />
        <el-table-column prop="stock" label="库存" width="80" />
        <el-table-column prop="sales" label="销量" width="80" />
        <el-table-column label="规格" width="90">
          <template #default="{ row }">{{ row.specs?.length ? row.specs.length + '组' : '-' }}</template>
        </el-table-column>
        <el-table-column label="上架" width="80">
          <template #default="{ row }">
            <el-switch :model-value="row.status === 1" @change="v => toggleStatus(row, v)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-link type="primary" @click="openFood(row)">编辑</el-link>
            <el-link type="danger" style="margin-left:10px" @click="delFood(row)">删除</el-link>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 菜品编辑弹窗 -->
    <el-dialog v-model="foodDialog" :title="form.id ? '编辑菜品' : '新增菜品'" width="620px" top="6vh">
      <el-form :model="form" label-width="90px">
        <el-form-item label="菜品名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="所属分类">
          <el-select v-model="form.category_id" style="width:100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="图片">
          <el-upload :action="'/api/upload'" name="file" :headers="upHeaders" :show-file-list="false"
                     :on-success="res => (form.image = res.url)" accept="image/*">
            <img v-if="form.image" :src="form.image" class="up-img" />
            <el-button v-else>上传图片</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="价格(¥)"><el-input-number v-model="form.price" :min="0.01" :precision="2" /></el-form-item>
        <el-form-item label="原价(¥)"><el-input-number v-model="form.original_price" :min="0" :precision="2" /></el-form-item>
        <el-form-item label="库存"><el-input-number v-model="form.stock" :min="0" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="上架状态"><el-switch v-model="foodStatus" /></el-form-item>

        <el-form-item label="规格/加料">
          <div class="specs-editor">
            <div v-for="(g, gi) in form.specs" :key="gi" class="spec-group">
              <div class="sg-head">
                <el-input v-model="g.name" placeholder="规格名（如：温度/份量）" style="width:200px" />
                <el-link type="danger" @click="form.specs.splice(gi, 1)">删除组</el-link>
              </div>
              <div v-for="(o, oi) in g.options" :key="oi" class="sg-opt">
                <el-input v-model="o.name" placeholder="选项名" style="width:160px" />
                <el-input-number v-model="o.price" :min="0" :precision="2" size="small" />
                <span class="text-muted">加价¥</span>
                <el-link type="danger" @click="g.options.splice(oi, 1)">删</el-link>
              </div>
              <el-link type="primary" @click="g.options.push({ name: '', price: 0 })">+ 添加选项</el-link>
            </div>
            <el-button size="small" @click="form.specs.push({ name: '', options: [{ name: '', price: 0 }] })">+ 添加规格组</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="foodDialog = false">取消</el-button>
        <el-button type="primary" @click="saveFood">保存</el-button>
      </template>
    </el-dialog>

    <!-- 分类弹窗 -->
    <el-dialog v-model="catDialog" :title="catForm.id ? '编辑分类' : '新增分类'" width="380px">
      <el-form :model="catForm" label-width="60px">
        <el-form-item label="名称"><el-input v-model="catForm.name" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="catForm.sort" :min="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="catDialog = false">取消</el-button>
        <el-button type="primary" @click="saveCat">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuth } from '../../stores/auth'
import { mGetCategories, mAddCategory, mUpdateCategory, mDeleteCategory,
         mGetFoods, mAddFood, mUpdateFood, mDeleteFood } from '../../api'

const auth = useAuth()
const upHeaders = { Authorization: 'Bearer ' + auth.token }
const categories = ref([])
const foods = ref([])
const query = reactive({ keyword: '', category_id: null })
const foodDialog = ref(false)
const catDialog = ref(false)
const foodStatus = ref(true)
const form = reactive({ id: 0, name: '', category_id: null, image: '', price: 1, original_price: 0, stock: 100, description: '', specs: [] })
const catForm = reactive({ id: 0, name: '', sort: 0 })

const catName = id => categories.value.find(c => c.id === id)?.name || '未分类'

async function loadCats() { categories.value = (await mGetCategories()).list }
async function load() { foods.value = (await mGetFoods(query)).list }

function openFood(row) {
  Object.assign(form, row ? {
    ...row, specs: JSON.parse(JSON.stringify(row.specs || []))
  } : { id: 0, name: '', category_id: categories.value[0]?.id, image: '', price: 1,
        original_price: 0, stock: 100, description: '', specs: [] })
  foodStatus.value = form.status !== 0
  foodDialog.value = true
}

async function saveFood() {
  if (!form.name) return ElMessage.warning('请填写菜品名称')
  const data = { ...form, status: foodStatus.value ? 1 : 0, specs: form.specs.filter(g => g.name && g.options.length) }
  if (form.id) await mUpdateFood(form.id, data)
  else await mAddFood(data)
  ElMessage.success('保存成功')
  foodDialog.value = false
  load()
}

async function toggleStatus(row, v) {
  await mUpdateFood(row.id, { ...row, status: v ? 1 : 0 })
  row.status = v ? 1 : 0
}

async function delFood(row) {
  await ElMessageBox.confirm(`确定删除菜品「${row.name}」？`, '提示', { type: 'warning' })
  await mDeleteFood(row.id)
  ElMessage.success('已删除')
  load()
}

function editCat(c) { Object.assign(catForm, c); catDialog.value = true }

async function saveCat() {
  if (!catForm.name) return ElMessage.warning('请填写分类名称')
  if (catForm.id) await mUpdateCategory(catForm.id, catForm)
  else await mAddCategory(catForm)
  ElMessage.success('保存成功')
  catDialog.value = false
  loadCats()
}

async function delCat(c) {
  await ElMessageBox.confirm(`确定删除分类「${c.name}」？`, '提示', { type: 'warning' })
  await mDeleteCategory(c.id)
  ElMessage.success('已删除')
  loadCats()
}

onMounted(async () => { await loadCats(); await load() })
</script>

<style scoped>
.foods-page { display: flex; gap: 16px; align-items: flex-start; }
.cat-card { width: 240px; flex-shrink: 0; }
.food-card { flex: 1; }
.card-head { display: flex; justify-content: space-between; align-items: center; }
.cat-row { display: flex; justify-content: space-between; padding: 10px 4px; border-bottom: 1px dashed #f0f0f0; }
.cat-ops { display: flex; gap: 12px; }
.tbl-img { width: 48px; height: 48px; border-radius: 6px; object-fit: cover; }
.up-img { width: 100px; height: 100px; border-radius: 8px; object-fit: cover; }
.specs-editor { width: 100%; }
.spec-group { border: 1px dashed #ddd; border-radius: 8px; padding: 10px; margin-bottom: 10px; }
.sg-head { display: flex; justify-content: space-between; margin-bottom: 8px; }
.sg-opt { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
</style>
