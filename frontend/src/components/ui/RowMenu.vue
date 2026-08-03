<script setup lang="ts">
import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuRoot,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from 'reka-ui'
import { Ellipsis } from '@lucide/vue'

export interface RowMenuItem {
  key: string
  label: string
  destructive?: boolean
}

const props = defineProps<{ items: RowMenuItem[] }>()
const emit = defineEmits<{ select: [key: string] }>()

const normalItems = () => props.items.filter((i) => !i.destructive)
const destructiveItems = () => props.items.filter((i) => i.destructive)
</script>

<template>
  <DropdownMenuRoot>
    <DropdownMenuTrigger
      class="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground data-[state=open]:bg-accent data-[state=open]:text-foreground cursor-pointer"
      aria-label="更多操作"
    >
      <Ellipsis class="size-4" />
    </DropdownMenuTrigger>
    <DropdownMenuPortal>
      <DropdownMenuContent
        align="end"
        :side-offset="4"
        class="z-50 min-w-36 rounded-lg border bg-popover p-1 text-popover-foreground shadow-md"
      >
        <DropdownMenuItem
          v-for="item in normalItems()"
          :key="item.key"
          class="cursor-pointer rounded-md px-3 py-2 text-sm outline-none transition-colors data-highlighted:bg-accent"
          @select="emit('select', item.key)"
        >
          {{ item.label }}
        </DropdownMenuItem>
        <template v-if="destructiveItems().length">
          <DropdownMenuSeparator class="my-1 h-px bg-border" />
          <DropdownMenuItem
            v-for="item in destructiveItems()"
            :key="item.key"
            class="cursor-pointer rounded-md px-3 py-2 text-sm text-destructive outline-none transition-colors data-highlighted:bg-destructive/10"
            @select="emit('select', item.key)"
          >
            {{ item.label }}
          </DropdownMenuItem>
        </template>
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>
</template>
