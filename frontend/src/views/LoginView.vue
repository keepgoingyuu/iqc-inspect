<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '../client'
import { currentUser } from '../store'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function onSubmit() {
  loading.value = true
  try {
    const { data, error } = await login({
      body: { username: username.value, password: password.value },
    })
    if (error || !data) {
      ElMessage.error('帳號或密碼錯誤')
      return
    }
    currentUser.value = data
    router.push('/')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <el-card class="login-card" header="登入">
      <el-form @submit.prevent="onSubmit">
        <el-form-item label="帳號">
          <el-input v-model="username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密碼">
          <el-input v-model="password" type="password" autocomplete="current-password" show-password />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">
          登入
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-wrap {
  display: flex;
  justify-content: center;
  padding-top: 10vh;
}
.login-card {
  width: 360px;
}
</style>
