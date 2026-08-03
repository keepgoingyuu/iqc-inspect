<script setup lang="ts">
import { useRouter } from 'vue-router'
import { logout } from './client'
import { currentUser } from './store'

const router = useRouter()

async function onLogout() {
  await logout()
  currentUser.value = null
  router.push('/login')
}
</script>

<template>
  <el-container class="app">
    <el-header class="header">
      <span class="title">IQC 進貨抽檢系統</span>
      <span v-if="currentUser" class="user">
        {{ currentUser.display_name }}({{ currentUser.role === 'supervisor' ? '主管' : '檢驗員' }})
        <el-button link type="primary" @click="onLogout">登出</el-button>
      </span>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<style>
body {
  margin: 0;
  font-family: 'Helvetica Neue', Arial, 'PingFang TC', 'Microsoft JhengHei', sans-serif;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #2b3a42;
  color: #fff;
}
.title {
  font-size: 18px;
  font-weight: bold;
}
.user {
  font-size: 14px;
}
</style>
