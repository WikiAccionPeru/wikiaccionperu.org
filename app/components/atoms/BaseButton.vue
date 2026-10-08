<script setup lang="ts">
defineProps<{ to?: string; variant?: 'solid' | 'outline' }>()
</script>
<template>
  <NuxtLink :to="to" class="btn" :class="variant ?? 'solid'"><slot /></NuxtLink>
</template>
<style scoped>
.btn { display: inline-block; padding: var(--space-2) var(--space-4); border-radius: 999px; border: 2px solid var(--color-text); text-decoration: none; font-weight: 500; }
.solid { background: var(--color-text); color: var(--color-bg); }
.outline { background: transparent; color: var(--color-text); }
.btn:hover { background: var(--color-accent-lilac); color: var(--color-text); }
</style>
