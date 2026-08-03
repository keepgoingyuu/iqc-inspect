<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { ShieldCheck } from '@lucide/vue'
import { login } from '../client'
import { currentUser } from '../store'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'

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
      toast.error('帳號或密碼錯誤')
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
  <div class="flex min-h-screen items-center justify-center bg-background px-4">
    <div class="w-full max-w-sm">
      <div class="mb-8 flex flex-col items-center gap-3">
        <div class="flex size-12 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-lg">
          <ShieldCheck class="size-6" />
        </div>
        <div class="text-center">
          <h1 class="text-xl font-semibold tracking-tight">IQC 進貨抽檢系統</h1>
          <p class="mt-1 text-sm text-muted-foreground">請登入以開始檢驗作業</p>
        </div>
      </div>

      <form
        class="space-y-4 rounded-xl border bg-card p-6 shadow-sm"
        @submit.prevent="onSubmit"
      >
        <div class="space-y-1.5">
          <label class="text-sm font-medium">帳號</label>
          <Input v-model="username" placeholder="qc01" autocomplete="username" />
        </div>
        <div class="space-y-1.5">
          <label class="text-sm font-medium">密碼</label>
          <Input v-model="password" type="password" autocomplete="current-password" />
        </div>
        <Button type="submit" class="w-full" :disabled="loading">
          {{ loading ? '登入中…' : '登入' }}
        </Button>
      </form>
    </div>
  </div>
</template>
