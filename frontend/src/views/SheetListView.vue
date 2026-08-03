<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { Plus } from '@lucide/vue'
import { createSheet, listSheets } from '../client'
import type { SheetListItem } from '../client'
import { statusLabel, statusVariant } from '../status'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Dialog from '@/components/ui/Dialog.vue'
import Input from '@/components/ui/Input.vue'

const router = useRouter()
const sheets = ref<SheetListItem[]>([])
const dialogOpen = ref(false)
const form = ref({ container_no: '', seal_no: '', unstuffing_date: '', qc_date: '' })

async function load() {
  const { data } = await listSheets()
  sheets.value = data ?? []
}

async function onCreate() {
  if (!form.value.container_no) {
    toast.warning('請輸入櫃號')
    return
  }
  const { data, error } = await createSheet({ body: form.value })
  if (error || !data) {
    toast.error('建立失敗')
    return
  }
  dialogOpen.value = false
  router.push(`/sheets/${data.id}`)
}

onMounted(load)
</script>

<template>
  <div class="mx-auto max-w-5xl">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight">檢驗單</h1>
        <p class="mt-1 text-sm text-muted-foreground">進貨/出貨抽檢紀錄</p>
      </div>
      <Button @click="dialogOpen = true">
        <Plus />
        新增檢驗單
      </Button>
    </div>

    <div class="overflow-hidden rounded-xl border bg-card shadow-sm">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b bg-muted/50 text-left text-xs text-muted-foreground">
            <th class="px-5 py-3 font-medium">#</th>
            <th class="px-5 py-3 font-medium">櫃號</th>
            <th class="px-5 py-3 font-medium">QC 日期</th>
            <th class="px-5 py-3 font-medium">狀態</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="sheet in sheets"
            :key="sheet.id"
            class="cursor-pointer border-b transition-colors last:border-0 hover:bg-accent/50"
            @click="router.push(`/sheets/${sheet.id}`)"
          >
            <td class="px-5 py-3.5 font-mono text-muted-foreground">{{ sheet.id }}</td>
            <td class="px-5 py-3.5 font-medium">{{ sheet.container_no }}</td>
            <td class="px-5 py-3.5 text-muted-foreground">{{ sheet.qc_date || '—' }}</td>
            <td class="px-5 py-3.5">
              <Badge :variant="statusVariant(sheet.status)">{{ statusLabel(sheet.status) }}</Badge>
            </td>
          </tr>
          <tr v-if="!sheets.length">
            <td colspan="4" class="px-5 py-12 text-center text-muted-foreground">
              尚無檢驗單,點右上角「新增檢驗單」開始
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Dialog v-model:open="dialogOpen" title="新增檢驗單">
      <div class="space-y-4">
        <div class="space-y-1.5">
          <label class="text-sm font-medium">櫃號 <span class="text-destructive">*</span></label>
          <Input v-model="form.container_no" placeholder="例:HRSU2253117" />
        </div>
        <div class="space-y-1.5">
          <label class="text-sm font-medium">封籤號</label>
          <Input v-model="form.seal_no" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="space-y-1.5">
            <label class="text-sm font-medium">拆櫃日期</label>
            <Input v-model="form.unstuffing_date" placeholder="YYYY-MM-DD" />
          </div>
          <div class="space-y-1.5">
            <label class="text-sm font-medium">QC 日期</label>
            <Input v-model="form.qc_date" placeholder="YYYY-MM-DD" />
          </div>
        </div>
      </div>
      <template #footer>
        <Button variant="ghost" @click="dialogOpen = false">取消</Button>
        <Button @click="onCreate">建立</Button>
      </template>
    </Dialog>
  </div>
</template>
