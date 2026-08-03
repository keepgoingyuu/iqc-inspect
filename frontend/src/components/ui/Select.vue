<script setup lang="ts">
import { cn } from '@/lib/utils'

// 內部工具用原生 select + Tailwind 樣式:少一層抽象、無障礙由瀏覽器保證
const props = defineProps<{ disabled?: boolean }>()
const model = defineModel<string | number>()
</script>

<template>
  <select
    v-model="model"
    :disabled="props.disabled"
    :class="
      cn(
        'flex h-9 w-full appearance-none rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60 [&>option]:bg-popover [&>option]:text-popover-foreground',
        $attrs.class as string,
      )
    "
  >
    <slot />
  </select>
</template>
