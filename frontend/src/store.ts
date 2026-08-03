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
