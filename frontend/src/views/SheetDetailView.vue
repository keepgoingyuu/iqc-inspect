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
  confirmMarking,
  getSheet,
  judgeSheet,
  listProducts,
  listSpecs,
  reject,
  runOcr,
  transitionSheet,
  updateItemValues,
  updateSample,
  uploadPdf,
  uploadPhoto,
} from '../client'
import type { ModelOut, PhotoOut, ProductOut, SampleOut, SheetOut, SpecOut } from '../client'
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
const products = ref<ProductOut[]>([])
const addModelOpen = ref(false)
const modelForm = ref({ product_id: 0, batch_code: '' })
const ocrLoading = ref<Record<number, boolean>>({})

const productsByCategory = computed(() => {
  const map = new Map<string, ProductOut[]>()
  for (const product of products.value.filter((p) => p.active)) {
    const list = map.get(product.category) ?? []
    list.push(product)
    map.set(product.category, list)
  }
  return map
})

const markingPhotos = (mi: ModelOut): PhotoOut[] =>
  (mi.samples ?? []).flatMap((s) => (s.photos ?? []).filter((p) => p.kind === 'marking'))

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
  if (!modelForm.value.product_id) {
    toast.warning('請選擇產品')
    return
  }
  const { error } = await addModel({ path: { sheet_id: sheetId }, body: modelForm.value })
  if (error) {
    toast.error(errDetail(error, '新增失敗'))
    return
  }
  addModelOpen.value = false
  modelForm.value = { product_id: 0, batch_code: '' }
  await load()
}

async function onRunOcr(photo: PhotoOut) {
  ocrLoading.value[photo.id] = true
  try {
    const { data, error } = await runOcr({ path: { photo_id: photo.id } })
    if (error) {
      toast.error(errDetail(error, '辨識失敗'))
      return
    }
    const result = data as any
    if (!result.available) {
      toast.warning('模型服務未啟動(Ollama),請人工比對')
    } else if (result.match) {
      toast.success(`🟢 辨識結果與預期標示一致:${result.ocr_text}`)
    } else {
      toast.warning(`🟡 辨識結果與預期不一致,請細看照片:${result.ocr_text}`)
    }
    await load()
  } finally {
    ocrLoading.value[photo.id] = false
  }
}

async function onConfirmMarking(mi: ModelOut, confirmed: boolean) {
  const { error } = await confirmMarking({
    path: { model_id: mi.id },
    body: { confirmed },
  })
  if (error) {
    toast.error(errDetail(error, '確認失敗'))
    return
  }
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

async function onUploadPhoto(sample: SampleOut, file: File, kind: 'part' | 'marking') {
  const { error } = await uploadPhoto({
    path: { sample_id: sample.id },
    query: { kind },
    body: { file },
  })
  if (error) toast.error('照片上傳失敗')
  else if (kind === 'marking') toast.success('主機板標示照已上傳(送審必備)')
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
  await Promise.all([
    load(),
    listSpecs().then(({ data }) => (specs.value = data ?? [])),
    listProducts().then(({ data }) => (products.value = data ?? [])),
  ])
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

      <!-- 主管審核:主機板標示比對關卡 -->
      <div
        v-if="sheet.status === 'pending_review'"
        class="mb-5 rounded-lg border-2 p-4"
        :class="mi.marking_confirmed ? 'border-success/50 bg-success/5' : 'border-warning/50 bg-warning/5'"
      >
        <div class="mb-3 flex items-center justify-between">
          <h3 class="text-sm font-semibold">主機板標示比對</h3>
          <Badge :variant="mi.marking_confirmed ? 'success' : 'warning'">
            {{ mi.marking_confirmed ? '已確認一致' : '待主管確認' }}
          </Badge>
        </div>
        <div class="mb-3">
          <span class="text-xs text-muted-foreground">預期標示(產品主檔)</span>
          <p class="font-mono text-lg font-semibold tracking-wide">
            {{ mi.expected_marking || '(未設定)' }}
          </p>
        </div>
        <div class="flex flex-wrap gap-3">
          <div v-for="photo in markingPhotos(mi)" :key="photo.id" class="w-52">
            <a :href="`/api/files/${photo.filename}`" target="_blank" title="點擊放大細看">
              <img :src="`/api/files/${photo.filename}`" class="h-36 w-full rounded-md border object-cover" />
            </a>
            <div class="mt-1.5 space-y-1">
              <Button
                size="sm"
                variant="outline"
                class="w-full"
                :disabled="ocrLoading[photo.id]"
                @click="onRunOcr(photo)"
              >
                {{ ocrLoading[photo.id] ? '辨識中…' : '🤖 模型辨識' }}
              </Button>
              <p v-if="photo.ocr_text" class="text-xs" :class="photo.ocr_match ? 'text-success' : 'text-warning'">
                {{ photo.ocr_match ? '🟢 一致' : '🟡 不一致,請細看' }}:
                <span class="font-mono">{{ photo.ocr_text }}</span>
              </p>
            </div>
          </div>
        </div>
        <div v-if="isSupervisor()" class="mt-4 border-t pt-3">
          <label class="flex cursor-pointer items-center gap-2 text-sm font-medium">
            <input
              type="checkbox"
              class="size-4 accent-[var(--success)]"
              :checked="mi.marking_confirmed"
              @change="(e: Event) => onConfirmMarking(mi, (e.target as HTMLInputElement).checked)"
            />
            我已比對照片,確認主機板型號與認證標示一致
          </label>
          <p class="mt-1 text-xs text-muted-foreground">
            模型辨識僅供參考;所有型號確認後才可簽核,勾選將記入稽核軌跡
          </p>
        </div>
      </div>

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
            <Button
              size="sm"
              variant="outline"
              title="匯入積分球測試報告,自動填入光電數據(只接受 .pdf)"
              @click="pickFile('.pdf', (f) => onUploadPdf(sample, f))"
            >
              <FileUp />匯入數據 PDF
            </Button>
            <Button
              size="sm"
              variant="outline"
              title="主機板標示特寫照 — 送審必備,主管審核比對用"
              @click="pickFile('image/*', (f) => onUploadPhoto(sample, f, 'marking'))"
            >
              <Camera />主機板標示照
            </Button>
            <Button
              size="sm"
              variant="outline"
              title="上傳拆解零件照片(JPG/PNG,手機可直接拍照)"
              @click="pickFile('image/*', (f) => onUploadPhoto(sample, f, 'part'))"
            >
              <Camera />零件照片
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
          <div v-for="photo in sample.photos" :key="photo.id" class="relative">
            <a :href="`/api/files/${photo.filename}`" target="_blank" title="點擊放大">
              <img
                :src="`/api/files/${photo.filename}`"
                :alt="photo.kind"
                class="h-28 rounded-md border object-cover"
                :class="photo.kind === 'marking' && 'ring-2 ring-warning'"
              />
            </a>
            <Badge
              v-if="photo.kind === 'marking'"
              variant="warning"
              class="absolute left-1 top-1"
            >
              標示
            </Badge>
          </div>
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

    <!-- 新增型號 Dialog:選產品,標準/參數/預期標示自動帶出 -->
    <Dialog v-model:open="addModelOpen" title="新增型號">
      <div class="space-y-4">
        <div class="space-y-1.5">
          <label class="text-sm font-medium">產品 <span class="text-destructive">*</span></label>
          <Select v-model="modelForm.product_id">
            <option :value="0" disabled>請選擇(類別標準與參數自動帶出)</option>
            <optgroup
              v-for="[category, items] in productsByCategory"
              :key="category"
              :label="category"
            >
              <option v-for="product in items" :key="product.id" :value="product.id">
                {{ product.name }}
              </option>
            </optgroup>
          </Select>
          <p class="text-xs text-muted-foreground">
            找不到產品?先到「產品主檔」建立型號與參數
          </p>
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
