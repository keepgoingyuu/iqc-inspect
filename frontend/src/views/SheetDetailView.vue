<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
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
import { RESULT_LABELS, statusLabel, statusTagType } from '../status'

const route = useRoute()
const sheetId = Number(route.params.id)
const sheet = ref<SheetOut | null>(null)
const specs = ref<SpecOut[]>([])
const addModelVisible = ref(false)
const modelForm = ref({ spec_template_id: 0, product_name: '', batch_code: '' })

const editable = computed(
  () => sheet.value && !['approved', 'rejected', 'defect_ticket', 'archived'].includes(sheet.value.status),
)

async function load() {
  const { data } = await getSheet({ path: { sheet_id: sheetId } })
  sheet.value = data ?? null
}

function specOf(mi: ModelOut): SpecOut | undefined {
  return specs.value.find((s) => s.id === mi.spec_template_id)
}

function itemsOf(mi: ModelOut): any[] {
  return (specOf(mi)?.items ?? []) as any[]
}

function isHighlighted(mi: ModelOut, key: string, seq?: number): boolean {
  const highlights = (mi.judgement as any)?.highlights ?? []
  return highlights.some(
    (h: any) => h.item === key && (seq === undefined || h.sample === seq),
  )
}

async function onAddModel() {
  if (!modelForm.value.spec_template_id || !modelForm.value.product_name) {
    ElMessage.warning('請選擇檢驗標準並輸入產品名稱')
    return
  }
  const { error } = await addModel({ path: { sheet_id: sheetId }, body: modelForm.value })
  if (error) {
    ElMessage.error(String((error as any).detail ?? '新增失敗'))
    return
  }
  addModelVisible.value = false
  await load()
}

async function onValueChange(mi: ModelOut, key: string, value: string | number) {
  await updateItemValues({ path: { model_id: mi.id }, body: { item_values: { [key]: value } } })
}

async function onAddSample(mi: ModelOut) {
  const nextSeq = Math.max(0, ...mi.samples!.map((s) => s.seq)) + 1
  const { error } = await addSample({ path: { model_id: mi.id }, body: { seq: nextSeq } })
  if (error) ElMessage.error(String((error as any).detail ?? '新增樣品失敗'))
  await load()
}

async function onUploadPdf(sample: SampleOut, file: File) {
  const { data, error } = await uploadPdf({
    path: { sample_id: sample.id },
    body: { file },
  })
  if (error || !data) {
    ElMessage.error(String((error as any)?.detail ?? 'PDF 解析失敗'))
    return
  }
  if (!data.has_text_layer) {
    ElMessage.warning('此 PDF 無文字層(圖片型),請人工輸入數據')
  } else if (data.missing.length) {
    ElMessage.warning(`部分欄位未解析到:${data.missing.join(', ')},請人工補填後確認`)
  } else {
    ElMessage.success('解析完成,請核對數值後按「確認數據」')
  }
  await load()
}

async function onPhotometricChange(sample: SampleOut, key: string, value: string) {
  const num = Number(value)
  if (Number.isNaN(num)) return
  await updateSample({ path: { sample_id: sample.id }, body: { photometric: { [key]: num } } })
}

async function onConfirmSample(sample: SampleOut) {
  await updateSample({ path: { sample_id: sample.id }, body: { confirmed: true } })
  ElMessage.success(`第 ${sample.seq} 件數據已確認`)
  await load()
}

async function onUploadPhoto(sample: SampleOut, file: File, kind: 'part' | 'certified') {
  const { error } = await uploadPhoto({
    path: { sample_id: sample.id },
    query: { kind },
    body: { file },
  })
  if (error) ElMessage.error('照片上傳失敗')
  await load()
}

async function onJudge() {
  const { error } = await judgeSheet({ path: { sheet_id: sheetId } })
  if (error) {
    ElMessage.error(String((error as any).detail ?? '判定失敗'))
    return
  }
  await load()
  ElMessage.success('綜合判定完成')
}

async function onTransition(to: string) {
  const { error } = await transitionSheet({
    path: { sheet_id: sheetId },
    body: { to_status: to },
  })
  if (error) {
    // 後端狀態機擋下(例:不合格未做二次拆檢)
    ElMessage.error(String((error as any).detail ?? '狀態轉移失敗'))
    return
  }
  await load()
}

async function onApprove() {
  const { error } = await approve({ path: { sheet_id: sheetId }, body: { comment: '' } })
  if (error) {
    ElMessage.error(String((error as any).detail ?? '簽核失敗'))
    return
  }
  await load()
  ElMessage.success('已簽核')
}

async function onReject() {
  const { error } = await reject({ path: { sheet_id: sheetId }, body: { comment: '' } })
  if (error) {
    ElMessage.error(String((error as any).detail ?? '退件失敗'))
    return
  }
  await load()
  ElMessage.warning('已退件並開立異常單')
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
  <div v-if="sheet">
    <div class="toolbar">
      <h2>
        檢驗單 #{{ sheet.id }} — 櫃號 {{ sheet.container_no }}
        <el-tag :type="statusTagType(sheet.status)">{{ statusLabel(sheet.status) }}</el-tag>
      </h2>
      <div>
        <el-button v-if="editable" @click="addModelVisible = true">新增型號</el-button>
        <el-button v-if="editable" type="primary" @click="onJudge">執行綜合判定</el-button>
        <el-button
          v-if="sheet.status === 'judged'"
          type="warning"
          @click="onTransition('second_inspection')"
        >
          啟動二次拆檢
        </el-button>
        <el-button
          v-if="['judged', 'second_inspection'].includes(sheet.status)"
          type="success"
          @click="onTransition('pending_review')"
        >
          送審
        </el-button>
        <template v-if="sheet.status === 'pending_review' && isSupervisor()">
          <el-button type="success" @click="onApprove">簽核通過</el-button>
          <el-button type="danger" @click="onReject">退件/開異常單</el-button>
        </template>
        <a
          v-if="['approved', 'archived'].includes(sheet.status)"
          :href="`/api/export/sheets/${sheet.id}/xlsx`"
        >
          <el-button type="primary">匯出 Excel</el-button>
        </a>
        <el-button v-if="sheet.status === 'approved'" @click="onTransition('archived')">
          結案歸檔
        </el-button>
      </div>
    </div>

    <el-card v-for="mi in sheet.model_inspections" :key="mi.id" class="model-card">
      <template #header>
        <b>{{ mi.product_name }}</b>
        <el-tag
          :type="mi.result === 'pass' ? 'success' : mi.result === 'fail' ? 'danger' : 'info'"
          style="margin-left: 8px"
        >
          {{ RESULT_LABELS[mi.result] }}
        </el-tag>
        <span class="batch">批號:{{ mi.batch_code || '—' }}</span>
      </template>

      <h4>檢驗項目</h4>
      <el-table :data="itemsOf(mi).filter((i: any) => !['auto', 'pdf'].includes(i.source_type))" size="small">
        <el-table-column label="項目" prop="label" width="220" />
        <el-table-column label="檢驗規範" prop="standard_text" width="200" />
        <el-table-column label="填寫">
          <template #default="{ row }">
            <template v-if="row.source_type === 'check'">
              <el-radio-group
                :model-value="(mi.item_values as any)[row.key]"
                :disabled="!editable"
                @update:model-value="(v: any) => onValueChange(mi, row.key, v)"
              >
                <el-radio-button value="OK">OK</el-radio-button>
                <el-radio-button value="NG">NG</el-radio-button>
              </el-radio-group>
            </template>
            <template v-else>
              <el-input
                :model-value="(mi.item_values as any)[row.key]"
                :disabled="!editable"
                style="width: 160px"
                :class="{ highlighted: isHighlighted(mi, row.key) }"
                @change="(v: string) => onValueChange(mi, row.key, v)"
              />
            </template>
            <el-tag v-if="isHighlighted(mi, row.key)" type="danger" size="small" class="hl-tag">
              異常
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <h4>
        樣品(積分球數據)
        <el-button v-if="editable" size="small" @click="onAddSample(mi)">+ 加入樣品</el-button>
      </h4>
      <el-card v-for="sample in mi.samples" :key="sample.id" class="sample-card" shadow="never">
        <template #header>
          <b>第 {{ sample.seq }} 件</b>
          <el-tag v-if="sample.seq > 1" type="warning" size="small">二次拆檢</el-tag>
          <el-tag v-if="sample.confirmed" type="success" size="small">數據已確認</el-tag>
          <el-tag v-else type="info" size="small">待確認</el-tag>
          <span v-if="sample.pdf_filename" class="pdf-name">{{ sample.pdf_filename }}</span>
        </template>
        <div class="sample-actions" v-if="editable">
          <el-button size="small" @click="pickFile('.pdf', (f) => onUploadPdf(sample, f))">
            上傳積分球 PDF
          </el-button>
          <el-button
            size="small"
            @click="pickFile('image/*', (f) => onUploadPhoto(sample, f, 'part'))"
          >
            上傳拆解照片
          </el-button>
          <el-button size="small" type="primary" :disabled="sample.confirmed" @click="onConfirmSample(sample)">
            確認數據
          </el-button>
        </div>
        <div class="photometric">
          <div
            v-for="item in itemsOf(mi).filter((i: any) => i.source_type === 'pdf')"
            :key="item.key"
            class="ph-field"
          >
            <label>{{ item.label }}<small>({{ item.standard_text }})</small></label>
            <el-input
              :model-value="(sample.photometric as any)[item.key]"
              :disabled="!editable"
              :class="{ highlighted: isHighlighted(mi, item.key, sample.seq) }"
              @change="(v: string) => onPhotometricChange(sample, item.key, v)"
            />
          </div>
        </div>
        <div v-if="sample.photos?.length" class="photos">
          <img
            v-for="photo in sample.photos"
            :key="photo.id"
            :src="`/api/files/${photo.filename}`"
            :alt="photo.kind"
          />
        </div>
      </el-card>
    </el-card>

    <el-dialog v-model="addModelVisible" title="新增型號" width="480px">
      <el-form label-width="90px">
        <el-form-item label="檢驗標準" required>
          <el-select v-model="modelForm.spec_template_id" style="width: 100%">
            <el-option
              v-for="spec in specs"
              :key="spec.id"
              :value="spec.id"
              :label="`${spec.name} (v${spec.version})`"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="產品名稱" required>
          <el-input v-model="modelForm.product_name" placeholder="例:LED 防潮灯 15W 曜弧黑" />
        </el-form-item>
        <el-form-item label="批號">
          <el-input v-model="modelForm.batch_code" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addModelVisible = false">取消</el-button>
        <el-button type="primary" @click="onAddModel">新增</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 8px;
}
.model-card {
  margin-bottom: 16px;
}
.batch {
  margin-left: 16px;
  color: #909399;
  font-size: 13px;
}
.sample-card {
  margin-bottom: 12px;
  background: #fafafa;
}
.sample-actions {
  margin-bottom: 12px;
}
.pdf-name {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}
.photometric {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.ph-field label {
  display: block;
  font-size: 13px;
  margin-bottom: 4px;
}
.ph-field small {
  color: #909399;
  margin-left: 4px;
}
/* 異常高亮:取代紙本的黃螢光筆 */
.highlighted :deep(.el-input__wrapper) {
  background: #fdedec;
  box-shadow: 0 0 0 1px #e74c3c inset;
}
.hl-tag {
  margin-left: 8px;
}
.photos img {
  height: 120px;
  margin: 8px 8px 0 0;
  border-radius: 4px;
  object-fit: cover;
}
</style>
