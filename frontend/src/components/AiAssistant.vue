<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Bot, Eraser, SendHorizontal, X } from '@lucide/vue'
import { chat } from '../client'
import Button from '@/components/ui/Button.vue'

const open = defineModel<boolean>('open', { default: false })
const route = useRoute()

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<Message[]>([])
const input = ref('')
const loading = ref(false)
const listEl = ref<HTMLElement | null>(null)
// 底部墊高:讓最新 query 有空間被推到可視區頂端(同 ChatGPT 做法)
const spacerHeight = ref(0)

const THINKING_PHRASES = [
  '正在為您整理回覆…',
  '正在分析您的問題…',
  '正在查閱檢驗數據…',
  '正在核對相關資料…',
  '正在彙整重點…',
  '正在確認細節…',
  '正在組織回答…',
  '正在檢視這張檢驗單…',
  '正在比對標準範圍…',
  '正在整理判定依據…',
  '稍候片刻,即將完成…',
  '正在為您找出關鍵資訊…',
]
const thinkingText = ref(THINKING_PHRASES[0])

// 在檢驗單頁時,把該單數據帶給助手當上下文
const sheetId = computed(() =>
  route.path.startsWith('/sheets/') ? Number(route.params.id) : undefined,
)

const suggestions = computed(() =>
  sheetId.value
    ? ['這張檢驗單有哪些異常項目?', '為什麼這個型號判不合格?', '這張單目前卡在哪個步驟?']
    : ['整個檢驗流程是怎麼走的?', '判定不合格之後要做什麼?', '主管審核時要確認什麼?'],
)

// 每輪問答:把最新的 query 捲到可視區最上方(答案在下面往下長)
async function scrollQueryToTop() {
  await nextTick()
  const container = listEl.value
  if (!container) return
  const queries = container.querySelectorAll<HTMLElement>('[data-role="user"]')
  const latest = queries[queries.length - 1]
  if (!latest) return
  // 先墊高底部,確保有足夠捲動空間能把 query 推到頂
  spacerHeight.value = Math.max(0, container.clientHeight - latest.offsetHeight - 96)
  await nextTick()
  // offsetTop 以定位祖先(aside)為基準,換算成容器內位置
  const top = latest.offsetTop - container.offsetTop - 12
  container.scrollTo({ top, behavior: 'smooth' })
}

async function send(text?: string) {
  const content = (text ?? input.value).trim()
  if (!content || loading.value) return
  input.value = ''
  messages.value.push({ role: 'user', content })
  thinkingText.value = THINKING_PHRASES[Math.floor(Math.random() * THINKING_PHRASES.length)]!
  loading.value = true
  await scrollQueryToTop()
  try {
    const { data } = await chat({
      body: { messages: messages.value, sheet_id: sheetId.value ?? null },
    })
    const result = data as any
    messages.value.push({
      role: 'assistant',
      content: result?.available
        ? result.reply
        : '⚠️ AI 助手服務未啟動(Ollama 未運行),請稍後再試。',
    })
  } catch {
    messages.value.push({ role: 'assistant', content: '⚠️ 發生錯誤,請再試一次。' })
  } finally {
    loading.value = false
    await scrollQueryToTop()
  }
}
</script>

<template>
  <transition name="drawer">
    <aside
      v-if="open"
      class="fixed inset-y-0 right-0 z-40 flex w-96 flex-col border-l bg-sidebar text-sidebar-foreground"
    >
      <!-- 標題列 -->
      <div class="flex items-center gap-2 border-b px-4 py-3">
        <Bot class="size-5" />
        <span class="flex-1 text-sm font-semibold">AI 助手</span>
        <button
          class="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground cursor-pointer"
          title="清空對話"
          @click="messages = []"
        >
          <Eraser class="size-4" />
        </button>
        <button
          class="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground cursor-pointer"
          title="關閉"
          @click="open = false"
        >
          <X class="size-4" />
        </button>
      </div>

      <!-- 訊息區 -->
      <div ref="listEl" class="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        <div class="rounded-lg bg-accent/60 p-3 text-sm leading-relaxed">
          👋 您好!我是檢驗系統的 AI 助手。
          <template v-if="sheetId">我已載入當前檢驗單的數據,</template>
          可以直接提問,或點下方預設問題開始。
        </div>

        <div v-if="!messages.length" class="space-y-2">
          <p class="text-xs text-muted-foreground">也許您想問</p>
          <button
            v-for="question in suggestions"
            :key="question"
            class="w-full rounded-lg border border-primary/30 bg-primary/5 px-3 py-2.5 text-left text-sm transition-colors hover:bg-primary/15 cursor-pointer"
            @click="send(question)"
          >
            {{ question }}
          </button>
        </div>

        <div
          v-for="(message, index) in messages"
          :key="index"
          class="flex"
          :data-role="message.role"
          :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div
            class="max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm leading-relaxed"
            :class="
              message.role === 'user'
                ? 'bg-primary text-primary-foreground'
                : 'bg-accent/60'
            "
          >
            {{ message.content }}
          </div>
        </div>

        <div v-if="loading" class="flex items-center gap-2 text-sm">
          <span class="shimmer-dot inline-block size-2 rounded-full"></span>
          <span class="shimmer-text font-medium">{{ thinkingText }}</span>
        </div>

        <!-- 底部墊高:讓最新 query 能被捲到頂 -->
        <div :style="{ height: spacerHeight + 'px' }"></div>
      </div>

      <!-- 輸入區 -->
      <div class="border-t px-4 py-3">
        <form class="flex items-center gap-2" @submit.prevent="send()">
          <input
            v-model="input"
            placeholder="傳送訊息…"
            class="h-9 flex-1 rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
          <Button type="submit" size="icon" :disabled="loading || !input.trim()">
            <SendHorizontal />
          </Button>
        </form>
        <p class="mt-1.5 text-center text-[11px] text-muted-foreground">
          AI 可能會出錯,請確認重要資訊;判定以系統規則為準。
        </p>
      </div>
    </aside>
  </transition>
</template>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: transform 0.2s ease;
}
.drawer-enter-from,
.drawer-leave-to {
  transform: translateX(100%);
}

/* 等待文字:彩色漸層流動(Apple Intelligence 風) */
.shimmer-text {
  background: linear-gradient(
    90deg,
    #6366f1,
    #a855f7,
    #ec4899,
    #f59e0b,
    #22c55e,
    #06b6d4,
    #6366f1
  );
  background-size: 300% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: shimmer-flow 2.5s linear infinite;
}
.shimmer-dot {
  background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899, #f59e0b, #6366f1);
  background-size: 300% 100%;
  animation: shimmer-flow 2.5s linear infinite;
}
@keyframes shimmer-flow {
  to {
    background-position: -300% 0;
  }
}
</style>
