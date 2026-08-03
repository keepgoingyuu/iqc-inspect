<script setup lang="ts">
import {
  DialogClose,
  DialogContent,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
} from 'reka-ui'
import { X } from '@lucide/vue'

defineProps<{ title: string }>()
const open = defineModel<boolean>('open', { default: false })
</script>

<template>
  <DialogRoot v-model:open="open">
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" />
      <DialogContent
        class="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border bg-popover p-6 text-popover-foreground shadow-lg focus:outline-none"
      >
        <div class="mb-4 flex items-center justify-between">
          <DialogTitle class="text-base font-semibold">{{ title }}</DialogTitle>
          <DialogClose
            class="rounded-md p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            <X class="size-4" />
          </DialogClose>
        </div>
        <slot />
        <div v-if="$slots.footer" class="mt-5 flex justify-end gap-2">
          <slot name="footer" />
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
