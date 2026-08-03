<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Toaster } from 'vue-sonner'
import {
  Bot,
  ClipboardList,
  LogOut,
  Moon,
  Package,
  Pin,
  ShieldCheck,
  Sun,
} from '@lucide/vue'
import { logout } from './client'
import { assistantOpen, currentUser } from './store'
import AiAssistant from './components/AiAssistant.vue'

const router = useRouter()
const route = useRoute()
const isDark = ref(document.documentElement.classList.contains('dark'))
const collapsed = ref(localStorage.getItem('sidebar') === 'collapsed')
const hovered = ref(false)

// 手機(<768px):側欄固定窄軌、無 hover 展開、助手全寬蓋板
const mobileQuery = window.matchMedia('(max-width: 767px)')
const isMobile = ref(mobileQuery.matches)
mobileQuery.addEventListener('change', (e) => (isMobile.value = e.matches))

// 收合時滑鼠移入 → 暫時展開(推擠內容);移開縮回;手機一律窄軌
const expanded = computed(() => !isMobile.value && (!collapsed.value || hovered.value))

const NAV_ITEMS = [
  { to: '/', label: '檢驗單', icon: ClipboardList, match: (p: string) => p === '/' || p.startsWith('/sheets') },
  { to: '/products', label: '產品主檔', icon: Package, match: (p: string) => p === '/products' },
]

// 頂部列即時時鐘
const now = ref(new Date())
let clockTimer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  clockTimer = setInterval(() => (now.value = new Date()), 1000)
})
onUnmounted(() => clearInterval(clockTimer))
const clock = computed(() =>
  now.value.toLocaleString('zh-TW', {
    year: 'numeric', month: 'numeric', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  }),
)

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

  <!-- 登入頁:無框架 -->
  <template v-if="route.path === '/login'">
    <router-view />
  </template>

  <div v-else class="flex min-h-screen">
    <!-- 側邊欄(可收合,hover 展開,推擠式) -->
    <aside
      class="fixed inset-y-0 left-0 z-40 flex flex-col border-r bg-sidebar text-sidebar-foreground transition-[width] duration-200"
      :class="expanded ? 'w-56' : 'w-14'"
      @mouseenter="hovered = true"
      @mouseleave="hovered = false"
    >
      <!-- 品牌列 + 釘選鈕 -->
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
          class="rounded-md p-1.5 transition-colors cursor-pointer"
          :class="
            collapsed
              ? 'text-muted-foreground hover:bg-accent hover:text-foreground'
              : 'bg-accent text-foreground'
          "
          :title="collapsed ? '釘選展開(固定不縮回)' : '取消釘選(自動縮回)'"
          @click="toggleSidebar"
        >
          <Pin class="size-4" />
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
    </aside>

    <!-- 頂部儀表板列 -->
    <header
      class="fixed top-0 right-0 z-30 flex h-14 items-center gap-2 border-b bg-sidebar px-3 transition-[left,right] duration-200 md:gap-3 md:px-5"
      :class="[
        expanded ? 'left-56' : 'left-14',
        assistantOpen && !isMobile ? 'right-96' : 'right-0',
      ]"
    >
      <span class="text-sm font-semibold">
        {{ route.path === '/products' ? '產品主檔' : '檢驗單' }}
      </span>
      <div class="flex-1"></div>

      <button
        class="rounded-full p-2 transition-colors cursor-pointer"
        :class="
          assistantOpen
            ? 'bg-primary text-primary-foreground'
            : 'bg-primary/15 text-primary hover:bg-primary/25'
        "
        title="AI 助手"
        @click="assistantOpen = !assistantOpen"
      >
        <Bot class="size-4" />
      </button>

      <button
        class="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground cursor-pointer"
        title="切換主題"
        @click="toggleTheme"
      >
        <Sun v-if="isDark" class="size-4" />
        <Moon v-else class="size-4" />
      </button>

      <span class="hidden font-mono text-sm text-muted-foreground lg:inline">{{ clock }}</span>

      <span
        v-if="currentUser"
        class="hidden rounded-full bg-success/15 px-3 py-1 text-xs font-medium text-success sm:inline"
      >
        {{ currentUser.display_name }}({{ currentUser.role === 'supervisor' ? '主管' : '檢驗員' }})
      </span>

      <button
        class="flex items-center gap-1.5 rounded-md px-2 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-destructive cursor-pointer"
        title="登出"
        @click="onLogout"
      >
        <LogOut class="size-4" />
        <span class="hidden sm:inline">登出</span>
      </button>
    </header>

    <!-- 主內容:推擠式,左右都讓位(手機:助手改全寬蓋板) -->
    <main
      class="flex-1 px-4 pb-6 pt-20 transition-[margin] duration-200 md:px-8"
      :class="[expanded ? 'ml-56' : 'ml-14', assistantOpen && !isMobile ? 'mr-96' : 'mr-0']"
    >
      <router-view />
    </main>

    <AiAssistant v-model:open="assistantOpen" />
  </div>
</template>
