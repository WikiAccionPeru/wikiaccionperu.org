<script setup lang="ts">
defineProps<{ to?: string }>()
</script>
<template>
  <NuxtLink :to="to" class="tag"><slot /></NuxtLink>
</template>
<style scoped>
.tag { display: inline-block; padding: 0 var(--space-2); border-radius: var(--radius); background: var(--color-bg-soft); font-size: var(--step--1); text-decoration: none; color: var(--color-text-muted); }
.tag:hover { background: var(--color-accent-cyan); }
</style>
