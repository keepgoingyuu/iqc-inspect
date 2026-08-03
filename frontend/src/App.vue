<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Toaster } from 'vue-sonner'
import {
  ClipboardList,
  LogOut,
  Moon,
  Package,
  PanelLeftClose,
  Pin,
  ShieldCheck,
  Sun,
} from '@lucide/vue'
import { logout } from './client'
import { currentUser } from './store'

const router = useRouter()
const route = useRoute()
const isDark = ref(document.documentElement.classList.contains('dark'))
const collapsed = ref(localStorage.getItem('sidebar') === 'collapsed')
const hovered = ref(false)
// 收合時滑鼠移入 → 暫時浮出展開(不推擠內容);移開縮回
const expanded = computed(() => !collapsed.value || hovered.value)

const NAV_ITEMS = [
  { to: '/', label: '檢驗單', icon: ClipboardList, match: (p: string) => p === '/' || p.startsWith('/sheets') },
  { to: '/products', label: '產品主檔', icon: Package, match: (p: string) => p === '/products' },
]

function toggleSidebar() {
  collapsed.value = !collapsed.value
  localStorage.setItem('sidebar', collapsed.value ? 'collapsed' : 'expanded')
}

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
    <!-- 側邊欄(可收合,仿 Cloudflare) -->
    <aside
      class="fixed inset-y-0 left-0 z-40 flex flex-col border-r bg-sidebar text-sidebar-foreground transition-[width] duration-200"
      :class="expanded ? 'w-56' : 'w-14'"
      @mouseenter="hovered = true"
      @mouseleave="hovered = false"
    >
      <!-- 品牌列 + 收合/釘選鈕 -->
      <div class="flex items-center gap-2.5 px-3 py-4" :class="!expanded && 'justify-center'">
        <div
          class="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground"
        >
          <ShieldCheck class="size-4.5" />
        </div>
        <div v-if="expanded" class="min-w-0 flex-1">
          <div class="truncate text-sm font-semibold leading-tight">IQC 進貨抽檢</div>
          <div class="text-[11px] text-muted-foreground">品質檢驗系統</div>
        </div>
        <button
          v-if="expanded"
          class="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground cursor-pointer"
          :title="collapsed ? '釘選展開(固定不縮回)' : '收合側邊欄'"
          @click="toggleSidebar"
        >
          <Pin v-if="collapsed" class="size-4" />
          <PanelLeftClose v-else class="size-4" />
        </button>
      </div>

      <!-- 導覽 -->
      <nav class="flex-1 space-y-1 px-2 pt-1">
        <router-link
          v-for="item in NAV_ITEMS"
          :key="item.to"
          :to="item.to"
          :title="!expanded ? item.label : undefined"
          class="flex items-center gap-2.5 rounded-md py-2 text-sm font-medium transition-colors"
          :class="[
            !expanded ? 'justify-center px-0' : 'px-3',
            item.match(route.path)
              ? 'bg-accent text-accent-foreground'
              : 'text-muted-foreground hover:bg-accent/60 hover:text-foreground',
          ]"
        >
          <component :is="item.icon" class="size-4 shrink-0" />
          <span v-if="expanded">{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- 使用者區 -->
      <div class="border-t px-2 py-3">
        <div
          v-if="currentUser"
          class="flex items-center gap-2"
          :class="!expanded ? 'justify-center' : 'px-1'"
        >
          <div
            class="flex size-8 shrink-0 items-center justify-center rounded-full bg-secondary text-xs font-semibold"
            :title="`${currentUser.display_name}(${currentUser.role === 'supervisor' ? '主管' : '檢驗員'})`"
          >
            {{ currentUser.display_name.slice(0, 1) }}
          </div>
          <template v-if="expanded">
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
          </template>
        </div>
      </div>
    </aside>

    <!-- 主內容 -->
    <!-- 推擠式:hover 展開時內容跟著讓位,不被遮住 -->
    <main
      class="flex-1 px-8 py-6 transition-[margin] duration-200"
      :class="expanded ? 'ml-56' : 'ml-14'"
    >
      <router-view />
    </main>
  </div>
</template>
