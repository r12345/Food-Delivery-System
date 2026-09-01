<template>
  <el-container class="admin-layout">
    <el-aside width="200px" class="aside">
      <div class="brand">乐享外卖 · 总后台</div>
      <el-menu :default-active="$route.path" router background-color="#141b2d" text-color="#bfcbd9"
               active-text-color="#409eff" class="menu">
        <el-menu-item index="/admin"><el-icon><DataAnalysis /></el-icon>数据大屏</el-menu-item>
        <el-menu-item index="/admin/users"><el-icon><User /></el-icon>用户管理</el-menu-item>
        <el-menu-item index="/admin/merchants"><el-icon><Shop /></el-icon>商家审核</el-menu-item>
        <el-menu-item index="/admin/orders"><el-icon><List /></el-icon>订单全局管理</el-menu-item>
        <el-menu-item index="/admin/riders"><el-icon><Bicycle /></el-icon>骑手管理</el-menu-item>
        <el-menu-item index="/admin/marketing"><el-icon><Present /></el-icon>营销管理</el-menu-item>
        <el-menu-item index="/admin/admins"><el-icon><Setting /></el-icon>系统权限</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span class="title">平台运营管理后台</span>
        <el-dropdown @command="cmd => cmd === 'logout' && doLogout()">
          <span class="admin-name">{{ auth.user?.nickname }}<el-icon><ArrowDown /></el-icon></span>
          <template #dropdown>
            <el-dropdown-menu><el-dropdown-item command="logout">退出登录</el-dropdown-item></el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="content"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { DataAnalysis, User, Shop, List, Bicycle, Present, Setting, ArrowDown } from '@element-plus/icons-vue'
import { useAuth } from '../stores/auth'

const router = useRouter()
const auth = useAuth()

function doLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout { height: 100vh; }
.aside { background: #141b2d; }
.brand { color: #fff; font-weight: 700; font-size: 16px; padding: 20px 16px; border-bottom: 1px solid rgba(255,255,255,.08); }
.menu { border-right: none; }
.header { background: #fff; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 1px 4px rgba(0,0,0,.06); }
.title { font-weight: 600; }
.admin-name { cursor: pointer; display: flex; align-items: center; gap: 4px; }
.content { background: #f5f6fa; overflow: auto; }
</style>
