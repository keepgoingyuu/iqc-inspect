import { ref } from 'vue'
import { me } from './client'
import type { UserOut } from './client'

export const currentUser = ref<UserOut | null>(null)

export async function loadCurrentUser(): Promise<UserOut | null> {
  const { data } = await me()
  currentUser.value = data ?? null
  return currentUser.value
}

export const isSupervisor = () => currentUser.value?.role === 'supervisor'

// AI 助手抽屜開關(各頁工具列的小按鈕共用)
export const assistantOpen = ref(false)
