<script setup lang="ts">
const props = defineProps<{ path: string; title: string; date: string; featuredMedia?: number; taxonomies?: Record<string, string[]> }>()
const { thumb, formatDate } = useSite()
const src = computed(() => thumb(props.featuredMedia))
</script>
<template>
  <article class="card">
    <NuxtLink :to="path" class="thumb" tabindex="-1" aria-hidden="true">
      <NuxtImg v-if="src" :src="src" alt="" width="360" height="360" fit="cover" loading="lazy" />
    </NuxtLink>
    <h2><NuxtLink :to="path"><span v-html="title" /></NuxtLink></h2>
    <time :datetime="date">{{ formatDate(date) }}</time>
    <TermLines :taxonomies="taxonomies" />
  </article>
</template>
<style scoped>
.card { display: flex; flex-direction: column; gap: var(--space-2); background: #fff; border: var(--border); padding: var(--space-3); height: 100%; }
.thumb { display: block; aspect-ratio: 1; border: var(--border); overflow: hidden; background: var(--color-bg-soft); }
.thumb img { width: 100%; height: 100%; object-fit: cover; }
h2 { margin: var(--space-2) 0 0; font-size: 1.25rem; line-height: 1.25; }
h2 a { text-decoration: none; }
time { color: var(--color-text-muted); font-size: 0.9rem; }
</style>
