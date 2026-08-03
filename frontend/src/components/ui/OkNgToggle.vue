<script setup lang="ts">
import { cn } from '@/lib/utils'

const props = defineProps<{ disabled?: boolean }>()
const model = defineModel<string>()
</script>

<template>
  <div class="inline-flex overflow-hidden rounded-md border border-input shadow-sm">
    <button
      type="button"
      :disabled="props.disabled"
      :class="
        cn(
          'px-3.5 py-1.5 text-xs font-semibold transition-colors cursor-pointer disabled:cursor-not-allowed',
          model === 'OK'
            ? 'bg-success text-white'
            : 'bg-transparent text-muted-foreground hover:bg-accent',
        )
      "
      @click="model = 'OK'"
    >
      OK
    </button>
    <button
      type="button"
      :disabled="props.disabled"
      :class="
        cn(
          'border-l border-input px-3.5 py-1.5 text-xs font-semibold transition-colors cursor-pointer disabled:cursor-not-allowed',
          model === 'NG'
            ? 'bg-destructive text-white'
            : 'bg-transparent text-muted-foreground hover:bg-accent',
        )
      "
      @click="model = 'NG'"
    >
      NG
    </button>
  </div>
</template>
