<script setup lang="ts">
import { cn } from '@/lib/utils'
</script>

<template>
  <div :class="cn('rounded-xl border bg-card text-card-foreground shadow-sm', $attrs.class as string)">
    <div v-if="$slots.header" class="flex items-center gap-2 border-b px-5 py-3.5">
      <slot name="header" />
    </div>
    <div class="px-5 py-4">
      <slot />
    </div>
    <div v-if="$slots.footer" class="border-t px-5 py-3.5">
      <slot name="footer" />
    </div>
  </div>
</template>
