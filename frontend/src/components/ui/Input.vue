<script setup lang="ts">
import { cn } from '@/lib/utils'

const props = defineProps<{
  type?: string
  placeholder?: string
  disabled?: boolean
  invalid?: boolean
}>()

const model = defineModel<string | number>()
</script>

<template>
  <input
    v-model="model"
    :type="props.type ?? 'text'"
    :placeholder="props.placeholder"
    :disabled="props.disabled"
    :class="
      cn(
        'flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60',
        props.invalid && 'border-destructive bg-destructive/10 focus-visible:ring-destructive',
        $attrs.class as string,
      )
    "
  />
</template>
