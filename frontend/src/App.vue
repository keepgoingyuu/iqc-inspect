<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Toaster } from 'vue-sonner'
import { ClipboardList, LogOut, Moon, ShieldCheck, Sun } from '@lucide/vue'
import { logout } from './client'
import { currentUser } from './store'

const router = useRouter()
const route = useRoute()
const isDark = ref(document.documentElement.classList.contains('dark'))

function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

async function onLogout() {
  await logout()
  currentUser.value = null
  router.push('/login')
}
</script>

<template>
  <Toaster rich-colors position="top-center" :theme="isDark ? 'dark' : 'light'" />

  <!-- 登入頁:無側邊欄 -->
  <template v-if="route.path === '/login'">
    <router-view />
  </template>

  <div v-else class="flex min-h-screen">
    <!-- 側邊欄 -->
    <aside
      class="fixed inset-y-0 left-0 z-40 flex w-56 flex-col border-r bg-sidebar text-sidebar-foreground"
    >
      <div class="flex items-center gap-2.5 px-5 py-5">
        <div class="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <ShieldCheck class="size-4.5" />
        </div>
        <div>
          <div class="text-sm font-semibold leading-tight">IQC 進貨抽檢</div>
          <div class="text-[11px] text-muted-foreground">品質檢驗系統</div>
        </div>
      </div>

      <nav class="flex-1 space-y-1 px-3 pt-2">
        <router-link
          to="/"
          class="flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors"
          :class="
            route.path === '/' || route.path.startsWith('/sheets')
              ? 'bg-accent text-accent-foreground'
              : 'text-muted-foreground hover:bg-accent/60 hover:text-foreground'
          "
        >
          <ClipboardList class="size-4" />
          檢驗單
        </router-link>
      </nav>

      <div class="border-t px-3 py-3">
        <div v-if="currentUser" class="flex items-center gap-2.5 px-2 py-1.5">
          <div
            class="flex size-8 items-center justify-center rounded-full bg-secondary text-xs font-semibold"
          >
            {{ currentUser.display_name.slice(0, 1) }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="truncate text-sm font-medium">{{ currentUser.display_name }}</div>
            <div class="text-[11px] text-muted-foreground">
              {{ currentUser.role === 'supervisor' ? '主管' : '檢驗員' }}
            </div>
          </div>
          <button
            class="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground cursor-pointer"
            title="切換主題"
            @click="toggleTheme"
          >
            <Sun v-if="isDark" class="size-4" />
            <Moon v-else class="size-4" />
          </button>
          <button
            class="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-destructive cursor-pointer"
            title="登出"
            @click="onLogout"
          >
            <LogOut class="size-4" />
          </button>
        </div>
      </div>
    </aside>

    <!-- 主內容 -->
    <main class="ml-56 flex-1 px-8 py-6">
      <router-view />
    </main>
  </div>
</template>
