<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createSheet, listSheets } from '../client'
import type { SheetListItem } from '../client'
import { statusLabel, statusTagType } from '../status'

const router = useRouter()
const sheets = ref<SheetListItem[]>([])
const dialogVisible = ref(false)
const form = ref({ container_no: '', seal_no: '', unstuffing_date: '', qc_date: '' })

async function load() {
  const { data } = await listSheets()
  sheets.value = data ?? []
}

async function onCreate() {
  if (!form.value.container_no) {
    ElMessage.warning('請輸入櫃號')
    return
  }
  const { data, error } = await createSheet({ body: form.value })
  if (error || !data) {
    ElMessage.error('建立失敗')
    return
  }
  dialogVisible.value = false
  router.push(`/sheets/${data.id}`)
}

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar">
      <h2>檢驗單列表</h2>
      <el-button type="primary" @click="dialogVisible = true">新增檢驗單</el-button>
    </div>

    <el-table :data="sheets" @row-click="(row: SheetListItem) => router.push(`/sheets/${row.id}`)">
      <el-table-column prop="id" label="#" width="70" />
      <el-table-column prop="container_no" label="櫃號" />
      <el-table-column prop="qc_date" label="QC 日期" />
      <el-table-column label="狀態" width="140">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="新增檢驗單" width="420px">
      <el-form label-width="90px">
        <el-form-item label="櫃號" required>
          <el-input v-model="form.container_no" placeholder="例:HRSU2253117" />
        </el-form-item>
        <el-form-item label="封籤號">
          <el-input v-model="form.seal_no" />
        </el-form-item>
        <el-form-item label="拆櫃日期">
          <el-input v-model="form.unstuffing_date" placeholder="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="QC 日期">
          <el-input v-model="form.qc_date" placeholder="YYYY-MM-DD" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onCreate">建立</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.el-table {
  cursor: pointer;
}
</style>
