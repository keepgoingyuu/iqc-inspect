<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { toast } from 'vue-sonner'
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  FileSpreadsheet,
  FileUp,
  Plus,
  Scale,
} from '@lucide/vue'
import {
  addModel,
  addSample,
  approve,
  getSheet,
  judgeSheet,
  listSpecs,
  reject,
  transitionSheet,
  updateItemValues,
  updateSample,
  uploadPdf,
  uploadPhoto,
} from '../client'
import type { ModelOut, SampleOut, SheetOut, SpecOut } from '../client'
import { isSupervisor } from '../store'
import { RESULT_LABELS, resultVariant, statusLabel, statusVariant } from '../status'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Dialog from '@/components/ui/Dialog.vue'
import Input from '@/components/ui/Input.vue'
import OkNgToggle from '@/components/ui/OkNgToggle.vue'
import Select from '@/components/ui/Select.vue'

const route = useRoute()
const sheetId = Number(route.params.id)
const sheet = ref<SheetOut | null>(null)
const specs = ref<SpecOut[]>([])
const addModelOpen = ref(false)
const modelForm = ref({ spec_template_id: 0, product_name: '', batch_code: '' })

const editable = computed(
  () =>
    sheet.value &&
    !['approved', 'rejected', 'defect_ticket', 'archived'].includes(sheet.value.status),
)

async function load() {
  const { data } = await getSheet({ path: { sheet_id: sheetId } })
  sheet.value = data ?? null
}

const specOf = (mi: ModelOut) => specs.value.find((s) => s.id === mi.spec_template_id)
const itemsOf = (mi: ModelOut) => (specOf(mi)?.items ?? []) as any[]
const manualItems = (mi: ModelOut) =>
  itemsOf(mi).filter((i: any) => !['auto', 'pdf'].includes(i.source_type))
const pdfItems = (mi: ModelOut) => itemsOf(mi).filter((i: any) => i.source_type === 'pdf')

function isHighlighted(mi: ModelOut, key: string, seq?: number): boolean {
  const highlights = (mi.judgement as any)?.highlights ?? []
  return highlights.some((h: any) => h.item === key && (seq === undefined || h.sample === seq))
}

function highlightReason(mi: ModelOut, key: string, seq?: number): string {
  const highlights = (mi.judgement as any)?.highlights ?? []
  const hit = highlights.find((h: any) => h.item === key && (seq === undefined || h.sample === seq))
  return hit?.reason ?? ''
}

const errDetail = (error: unknown, fallback: string) =>
  String((error as any)?.detail ?? fallback)

async function onAddModel() {
  if (!modelForm.value.spec_template_id || !modelForm.value.product_name) {
    toast.warning('請選擇檢驗標準並輸入產品名稱')
    return
  }
  const { error } = await addModel({ path: { sheet_id: sheetId }, body: modelForm.value })
  if (error) {
    toast.error(errDetail(error, '新增失敗'))
    return
  }
  addModelOpen.value = false
  modelForm.value = { spec_template_id: 0, product_name: '', batch_code: '' }
  await load()
}

async function onValueChange(mi: ModelOut, key: string, value: string | number | undefined) {
  if (value === undefined) return
  ;(mi.item_values as any)[key] = value // 樂觀更新:畫面立即反應,再同步後端
  const { error } = await updateItemValues({
    path: { model_id: mi.id },
    body: { item_values: { [key]: value } },
  })
  if (error) {
    toast.error(errDetail(error, '儲存失敗'))
    await load() // 失敗時還原為後端狀態
  }
}

async function onAddSample(mi: ModelOut) {
  const nextSeq = Math.max(0, ...mi.samples!.map((s) => s.seq)) + 1
  const { error } = await addSample({ path: { model_id: mi.id }, body: { seq: nextSeq } })
  if (error) toast.error(errDetail(error, '新增樣品失敗'))
  await load()
}

async function onUploadPdf(sample: SampleOut, file: File) {
  const { data, error } = await uploadPdf({ path: { sample_id: sample.id }, body: { file } })
  if (error || !data) {
    toast.error(errDetail(error, 'PDF 解析失敗'))
    return
  }
  if (!data.has_text_layer) {
    toast.warning('此 PDF 無文字層(圖片型),請人工輸入數據')
  } else if (data.missing.length) {
    toast.warning(`部分欄位未解析到:${data.missing.join(', ')},請人工補填後確認`)
  } else {
    toast.success('解析完成,請核對數值後按「確認數據」')
  }
  await load()
}

async function onPhotometricChange(sample: SampleOut, key: string, value: string | number | undefined) {
  const num = Number(value)
  if (value === undefined || Number.isNaN(num)) return
  ;(sample.photometric as any)[key] = num // 樂觀更新
  const { error } = await updateSample({
    path: { sample_id: sample.id },
    body: { photometric: { [key]: num } },
  })
  if (error) {
    toast.error(errDetail(error, '儲存失敗'))
    await load()
  }
}

async function onConfirmSample(sample: SampleOut) {
  await updateSample({ path: { sample_id: sample.id }, body: { confirmed: true } })
  toast.success(`第 ${sample.seq} 件數據已確認`)
  await load()
}

async function onUploadPhoto(sample: SampleOut, file: File) {
  const { error } = await uploadPhoto({
    path: { sample_id: sample.id },
    query: { kind: 'part' },
    body: { file },
  })
  if (error) toast.error('照片上傳失敗')
  await load()
}

async function onJudge() {
  const { error } = await judgeSheet({ path: { sheet_id: sheetId } })
  if (error) {
    toast.error(errDetail(error, '判定失敗'))
    return
  }
  await load()
  toast.success('綜合判定完成')
}

async function onTransition(to: string) {
  const { error } = await transitionSheet({
    path: { sheet_id: sheetId },
    body: { to_status: to },
  })
  if (error) {
    // 後端狀態機擋下(例:不合格未做二次拆檢)
    toast.error(errDetail(error, '狀態轉移失敗'))
    return
  }
  await load()
}

async function onApprove() {
  const { error } = await approve({ path: { sheet_id: sheetId }, body: { comment: '' } })
  if (error) {
    toast.error(errDetail(error, '簽核失敗'))
    return
  }
  await load()
  toast.success('已簽核')
}

async function onReject() {
  const { error } = await reject({ path: { sheet_id: sheetId }, body: { comment: '' } })
  if (error) {
    toast.error(errDetail(error, '退件失敗'))
    return
  }
  await load()
  toast.warning('已退件並開立異常單')
}

function pickFile(accept: string, callback: (file: File) => void) {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = accept
  input.onchange = () => {
    if (input.files?.[0]) callback(input.files[0])
  }
  input.click()
}

onMounted(async () => {
  await Promise.all([load(), listSpecs().then(({ data }) => (specs.value = data ?? []))])
})
</script>

<template>
  <div v-if="sheet" class="mx-auto max-w-5xl">
    <!-- 頁首 -->
    <div class="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        <div class="flex items-center gap-3">
          <h1 class="text-2xl font-semibold tracking-tight">檢驗單 #{{ sheet.id }}</h1>
          <Badge :variant="statusVariant(sheet.status)">{{ statusLabel(sheet.status) }}</Badge>
        </div>
        <p class="mt-1 text-sm text-muted-foreground">
          櫃號 {{ sheet.container_no }}
          <template v-if="sheet.seal_no"> · 封籤 {{ sheet.seal_no }}</template>
          <template v-if="sheet.qc_date"> · QC {{ sheet.qc_date }}</template>
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button v-if="editable" variant="outline" @click="addModelOpen = true">
          <Plus />新增型號
        </Button>
        <Button v-if="editable" @click="onJudge">
          <Scale />執行綜合判定
        </Button>
        <Button
          v-if="sheet.status === 'judged'"
          variant="secondary"
          @click="onTransition('second_inspection')"
        >
          啟動二次拆檢
        </Button>
        <Button
          v-if="['judged', 'second_inspection'].includes(sheet.status)"
          variant="success"
          @click="onTransition('pending_review')"
        >
          送審
        </Button>
        <template v-if="sheet.status === 'pending_review' && isSupervisor()">
          <Button variant="success" @click="onApprove"><CheckCircle2 />簽核通過</Button>
          <Button variant="destructive" @click="onReject">退件/開異常單</Button>
        </template>
        <a
          v-if="['approved', 'archived'].includes(sheet.status)"
          :href="`/api/export/sheets/${sheet.id}/xlsx`"
        >
          <Button variant="outline"><FileSpreadsheet />匯出 Excel</Button>
        </a>
        <Button v-if="sheet.status === 'approved'" variant="ghost" @click="onTransition('archived')">
          結案歸檔
        </Button>
      </div>
    </div>

    <!-- 型號卡片 -->
    <Card v-for="mi in sheet.model_inspections" :key="mi.id" class="mb-5">
      <template #header>
        <span class="font-semibold">{{ mi.product_name }}</span>
        <Badge :variant="resultVariant(mi.result)">{{ RESULT_LABELS[mi.result] }}</Badge>
        <span class="ml-auto text-xs text-muted-foreground">批號 {{ mi.batch_code || '—' }}</span>
      </template>

      <!-- 檢驗項目(手動/勾選) -->
      <h3 class="mb-3 text-sm font-semibold text-muted-foreground">檢驗項目</h3>
      <div class="mb-6 overflow-hidden rounded-lg border">
        <table class="w-full text-sm">
          <tbody>
            <tr
              v-for="item in manualItems(mi)"
              :key="item.key"
              class="border-b last:border-0"
              :class="isHighlighted(mi, item.key) && 'bg-destructive/5'"
            >
              <td class="w-56 px-4 py-2.5 font-medium">{{ item.label }}</td>
              <td class="w-48 px-4 py-2.5 text-xs text-muted-foreground">
                {{ item.standard_text }}
              </td>
              <td class="px-4 py-2.5">
                <div class="flex items-center gap-2">
                  <OkNgToggle
                    v-if="item.source_type === 'check'"
                    :model-value="(mi.item_values as any)[item.key]"
                    :disabled="!editable"
                    @update:model-value="(v?: string) => onValueChange(mi, item.key, v)"
                  />
                  <Input
                    v-else
                    :model-value="(mi.item_values as any)[item.key]"
                    :disabled="!editable"
                    :invalid="isHighlighted(mi, item.key)"
                    class="max-w-40"
                    @change="(e: Event) => onValueChange(mi, item.key, (e.target as HTMLInputElement).value)"
                  />
                  <span
                    v-if="isHighlighted(mi, item.key)"
                    class="flex items-center gap-1 text-xs text-destructive"
                  >
                    <AlertTriangle class="size-3.5" />{{ highlightReason(mi, item.key) }}
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 樣品 -->
      <div class="mb-3 flex items-center justify-between">
        <h3 class="text-sm font-semibold text-muted-foreground">樣品(積分球數據)</h3>
        <Button v-if="editable" size="sm" variant="outline" @click="onAddSample(mi)">
          <Plus />加入樣品
        </Button>
      </div>

      <div
        v-for="sample in mi.samples"
        :key="sample.id"
        class="mb-3 rounded-lg border bg-muted/30 p-4 last:mb-0"
      >
        <div class="mb-3 flex flex-wrap items-center gap-2">
          <span class="font-medium">第 {{ sample.seq }} 件</span>
          <Badge v-if="sample.seq > 1" variant="warning">二次拆檢</Badge>
          <Badge v-if="sample.confirmed" variant="success">數據已確認</Badge>
          <Badge v-else variant="muted">待確認</Badge>
          <span v-if="sample.pdf_filename" class="text-xs text-muted-foreground">
            {{ sample.pdf_filename }}
          </span>
          <div v-if="editable" class="ml-auto flex gap-2">
            <Button size="sm" variant="outline" @click="pickFile('.pdf', (f) => onUploadPdf(sample, f))">
              <FileUp />積分球 PDF
            </Button>
            <Button size="sm" variant="outline" @click="pickFile('image/*', (f) => onUploadPhoto(sample, f))">
              <Camera />拆解照片
            </Button>
            <Button size="sm" :disabled="sample.confirmed" @click="onConfirmSample(sample)">
              確認數據
            </Button>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 md:grid-cols-3">
          <div v-for="item in pdfItems(mi)" :key="item.key">
            <label class="mb-1 block text-xs font-medium">
              {{ item.label }}
              <span class="text-muted-foreground">({{ item.standard_text }})</span>
            </label>
            <Input
              :model-value="(sample.photometric as any)[item.key]"
              :disabled="!editable"
              :invalid="isHighlighted(mi, item.key, sample.seq)"
              @change="(e: Event) => onPhotometricChange(sample, item.key, (e.target as HTMLInputElement).value)"
            />
            <p
              v-if="isHighlighted(mi, item.key, sample.seq)"
              class="mt-1 flex items-center gap-1 text-xs text-destructive"
            >
              <AlertTriangle class="size-3" />{{ highlightReason(mi, item.key, sample.seq) }}
            </p>
          </div>
        </div>

        <div v-if="sample.photos?.length" class="mt-3 flex flex-wrap gap-2">
          <img
            v-for="photo in sample.photos"
            :key="photo.id"
            :src="`/api/files/${photo.filename}`"
            :alt="photo.kind"
            class="h-28 rounded-md border object-cover"
          />
        </div>
      </div>
      <p v-if="!mi.samples?.length" class="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
        尚無樣品,點「加入樣品」後上傳積分球 PDF 或人工輸入數據
      </p>
    </Card>

    <p
      v-if="!sheet.model_inspections?.length"
      class="rounded-xl border border-dashed p-12 text-center text-muted-foreground"
    >
      尚未加入型號,點右上角「新增型號」開始檢驗
    </p>

    <!-- 新增型號 Dialog -->
    <Dialog v-model:open="addModelOpen" title="新增型號">
      <div class="space-y-4">
        <div class="space-y-1.5">
          <label class="text-sm font-medium">檢驗標準 <span class="text-destructive">*</span></label>
          <Select v-model="modelForm.spec_template_id">
            <option :value="0" disabled>請選擇</option>
            <option v-for="spec in specs" :key="spec.id" :value="spec.id">
              {{ spec.name }}(v{{ spec.version }})
            </option>
          </Select>
        </div>
        <div class="space-y-1.5">
          <label class="text-sm font-medium">產品名稱 <span class="text-destructive">*</span></label>
          <Input v-model="modelForm.product_name" placeholder="例:LED 防潮灯 15W 曜弧黑" />
        </div>
        <div class="space-y-1.5">
          <label class="text-sm font-medium">批號</label>
          <Input v-model="modelForm.batch_code" />
        </div>
      </div>
      <template #footer>
        <Button variant="ghost" @click="addModelOpen = false">取消</Button>
        <Button @click="onAddModel">新增</Button>
      </template>
    </Dialog>
  </div>
</template>
