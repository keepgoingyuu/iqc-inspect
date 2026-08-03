<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { toast } from 'vue-sonner'
import { Plus, ImageUp } from '@lucide/vue'
import { createProduct, listProducts, listSpecs, uploadCertPhoto } from '../client'
import type { ProductOut, SpecOut } from '../client'
import { isSupervisor } from '../store'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Dialog from '@/components/ui/Dialog.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'

const products = ref<ProductOut[]>([])
const specs = ref<SpecOut[]>([])
const dialogOpen = ref(false)
const form = ref({ name: '', category: '', expected_marking: '' })
const paramValues = ref<Record<string, string>>({})

const PARAM_LABELS: Record<string, string> = {
  nominal_power: '標稱功率(W)',
  cct_nominal: '標稱色溫(K)',
  cct_min: '色溫下限(K)',
  cct_max: '色溫上限(K)',
  flux_min: '光通量下限(lm)',
  flux_max: '光通量上限(lm)',
  efficacy_min: '光效下限(lm/W)',
  efficacy_max: '光效上限(lm/W)',
  net_weight_nominal: '標稱淨重(g)',
  box_weight_nominal: '標稱外箱重(kg)',
}
const paramLabel = (key: string) => PARAM_LABELS[key] ?? key

const categories = computed(() => [...new Set(specs.value.map((s) => s.product_category))])

// 從所選類別的標準公式裡,抽出需要填的參數欄位
const paramKeys = computed(() => {
  const spec = specs.value.find((s) => s.product_category === form.value.category)
  if (!spec) return []
  const keys = new Set<string>()
  for (const item of (spec.items ?? []) as any[]) {
    const rule = item.rule ?? {}
    for (const field of ['param', 'param_min', 'param_max']) {
      if (rule[field]) keys.add(rule[field])
    }
  }
  return [...keys]
})

const grouped = computed(() => {
  const map = new Map<string, ProductOut[]>()
  for (const product of products.value) {
    const list = map.get(product.category) ?? []
    list.push(product)
    map.set(product.category, list)
  }
  return map
})

async function load() {
  const [productsResult, specsResult] = await Promise.all([listProducts(), listSpecs()])
  products.value = productsResult.data ?? []
  specs.value = specsResult.data ?? []
}

async function onCreate() {
  if (!form.value.name || !form.value.category) {
    toast.warning('請填寫型號名稱並選擇類別')
    return
  }
  const params: Record<string, number> = {}
  for (const [key, raw] of Object.entries(paramValues.value)) {
    const num = Number(raw)
    if (raw !== '' && !Number.isNaN(num)) params[key] = num
  }
  const { error } = await createProduct({ body: { ...form.value, params } })
  if (error) {
    toast.error(String((error as any).detail ?? '建立失敗'))
    return
  }
  toast.success('產品已建立')
  dialogOpen.value = false
  form.value = { name: '', category: '', expected_marking: '' }
  paramValues.value = {}
  await load()
}

function pickCertPhoto(product: ProductOut) {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = async () => {
    if (!input.files?.[0]) return
    const { error } = await uploadCertPhoto({
      path: { product_id: product.id },
      body: { file: input.files[0] },
    })
    if (error) toast.error('認證照上傳失敗')
    else toast.success('認證照已上傳')
    await load()
  }
  input.click()
}

onMounted(load)
</script>

<template>
  <div class="mx-auto max-w-5xl">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight">產品主檔</h1>
        <p class="mt-1 text-sm text-muted-foreground">
          型號的標稱參數與主機板標示 — 檢驗時自動帶出,主檔更新不影響歷史檢驗單
        </p>
      </div>
      <Button v-if="isSupervisor()" @click="dialogOpen = true"><Plus />新增產品</Button>
    </div>

    <div v-for="[category, items] in grouped" :key="category" class="mb-6">
      <h2 class="mb-2 text-sm font-semibold text-muted-foreground">{{ category }}</h2>
      <div class="overflow-hidden rounded-xl border bg-card shadow-sm">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b bg-muted/50 text-left text-xs text-muted-foreground">
              <th class="px-5 py-3 font-medium">型號</th>
              <th class="px-5 py-3 font-medium">預期主機板標示</th>
              <th class="px-5 py-3 font-medium">參數</th>
              <th class="px-5 py-3 font-medium">認證照</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="product in items" :key="product.id" class="border-b last:border-0">
              <td class="px-5 py-3.5 font-medium">
                {{ product.name }}
                <Badge v-if="!product.active" variant="muted" class="ml-2">停用</Badge>
              </td>
              <td class="px-5 py-3.5 font-mono text-xs">
                {{ product.expected_marking || '—' }}
              </td>
              <td class="px-5 py-3.5 text-xs text-muted-foreground">
                {{ Object.entries(product.params).map(([k, v]) => `${paramLabel(k)}=${v}`).join('、') || '—' }}
              </td>
              <td class="px-5 py-3.5">
                <div class="flex items-center gap-2">
                  <img
                    v-for="photo in product.cert_photos"
                    :key="photo.id"
                    :src="`/api/files/${photo.filename}`"
                    class="h-10 w-10 rounded border object-cover"
                  />
                  <Button
                    v-if="isSupervisor()"
                    size="sm"
                    variant="ghost"
                    title="上傳認證照(選填)"
                    @click="pickCertPhoto(product)"
                  >
                    <ImageUp />
                  </Button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <p v-if="!products.length" class="rounded-xl border border-dashed p-12 text-center text-muted-foreground">
      尚無產品,主管可點右上角「新增產品」
    </p>

    <Dialog v-model:open="dialogOpen" title="新增產品">
      <div class="max-h-[60vh] space-y-4 overflow-y-auto pr-1">
        <div class="space-y-1.5">
          <label class="text-sm font-medium">類別 <span class="text-destructive">*</span></label>
          <Select v-model="form.category">
            <option value="" disabled>請選擇(對應檢驗標準)</option>
            <option v-for="category in categories" :key="category" :value="category">
              {{ category }}
            </option>
          </Select>
        </div>
        <div class="space-y-1.5">
          <label class="text-sm font-medium">型號名稱 <span class="text-destructive">*</span></label>
          <Input v-model="form.name" placeholder="例:LED 防潮灯 24W 曜弧黑" />
        </div>
        <div class="space-y-1.5">
          <label class="text-sm font-medium">預期主機板標示</label>
          <Input v-model="form.expected_marking" placeholder="例:5205-G4-0240-3VC0101" class="font-mono" />
          <p class="text-xs text-muted-foreground">審核時主管以此字串比對主機板照片</p>
        </div>
        <template v-if="paramKeys.length">
          <p class="text-sm font-medium">標稱參數(套入類別標準公式)</p>
          <div class="grid grid-cols-2 gap-3">
            <div v-for="key in paramKeys" :key="key" class="space-y-1">
              <label class="text-xs">{{ paramLabel(key) }}</label>
              <Input v-model="paramValues[key]" type="number" />
            </div>
          </div>
        </template>
      </div>
      <template #footer>
        <Button variant="ghost" @click="dialogOpen = false">取消</Button>
        <Button @click="onCreate">建立</Button>
      </template>
    </Dialog>
  </div>
</template>
