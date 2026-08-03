export const STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  data_entered: '數據已錄入',
  judged: '已判定',
  second_inspection: '二次拆檢中',
  pending_review: '待審核',
  approved: '已簽核',
  rejected: '退件',
  defect_ticket: '異常單',
  archived: '已歸檔',
}

export const statusLabel = (status: string) => STATUS_LABELS[status] ?? status

export function statusTagType(
  status: string,
): 'primary' | 'success' | 'warning' | 'danger' | 'info' {
  switch (status) {
    case 'approved':
      return 'success'
    case 'second_inspection':
    case 'pending_review':
      return 'warning'
    case 'rejected':
    case 'defect_ticket':
      return 'danger'
    case 'archived':
      return 'info'
    default:
      return 'primary'
  }
}

export const RESULT_LABELS: Record<string, string> = {
  pending: '未判定',
  pass: '合格',
  fail: '不合格',
}
