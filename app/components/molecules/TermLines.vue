<script setup lang="ts">
const props = defineProps<{ taxonomies?: Record<string, string[]>; maxTags?: number }>()
const { term } = useSite()
const pick = (tax: string, max = 6) => (props.taxonomies?.[tax] ?? []).slice(0, max).map((s) => term(tax, s)).filter((t): t is NonNullable<typeof t> => !!t)
const rows = computed(() => [
  { icon: '◎', label: 'Enfoque', items: pick('enfoque_tematico') },
  { icon: '▪', label: 'Categorías', items: pick('category') },
  { icon: '#', label: 'Etiquetas', items: pick('post_tag', props.maxTags ?? 8) },
].filter((r) => r.items.length))
</script>
<template>
  <div class="terms">
    <p v-for="r in rows" :key="r.label"><span :aria-label="r.label">{{ r.icon }}</span>
      <template v-for="(t, i) in r.items" :key="t.to"><NuxtLink :to="t.to">{{ t.name }}</NuxtLink><template v-if="i < r.items.length - 1">, </template></template>
    </p>
  </div>
</template>
<style scoped>
.terms { font-size: 0.72rem; line-height: 1.5; }
.terms p { margin: 0 0 var(--space-1); }
.terms a { text-decoration: none; } .terms a:hover { text-decoration: underline; }
</style>
