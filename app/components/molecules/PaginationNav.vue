<script setup lang="ts">
const props = defineProps<{ page: number; pages: number; base: string }>()
const href = (n: number) => (n === 1 ? props.base : `${props.base}page/${n}/`)
const items = computed(() => {
  const set = new Set([1, props.pages, props.page - 1, props.page, props.page + 1].filter((n) => n >= 1 && n <= props.pages))
  const out: (number | '…')[] = []
  ;[...set].sort((a, b) => a - b).forEach((n, i, arr) => { if (i && n - arr[i - 1] > 1) out.push('…'); out.push(n) })
  return out
})
</script>
<template>
  <nav v-if="pages > 1" class="pager" aria-label="Paginación">
    <NuxtLink v-if="page > 1" :to="href(page - 1)" rel="prev">← Anterior</NuxtLink>
    <template v-for="(n, i) in items" :key="i">
      <span v-if="n === '…'">…</span>
      <span v-else-if="n === page" aria-current="page" class="current">{{ n }}</span>
      <NuxtLink v-else :to="href(n)">{{ n }}</NuxtLink>
    </template>
    <NuxtLink v-if="page < pages" :to="href(page + 1)" rel="next">Siguiente →</NuxtLink>
  </nav>
</template>
<style scoped>
.pager { display: flex; flex-wrap: wrap; gap: var(--space-3); justify-content: center; margin-top: var(--space-5); }
.current { font-weight: 700; border-bottom: 3px solid var(--color-accent-lilac); }
</style>
