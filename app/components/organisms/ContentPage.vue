<script setup lang="ts">
const props = withDefaults(defineProps<{ path: string; seo?: boolean }>(), { seo: true })
const { formatDate, term } = useSite()
const { data: doc } = await useAsyncData(`doc-${props.path}`, () => queryCollection('content').path(props.path).first())
if (!doc.value) throw createError({ statusCode: 404, statusMessage: 'Page not found', fatal: true })
if (props.seo) useSeoMeta({ title: () => `${doc.value?.title} — WikiAcción Perú`.replace(/&amp;/g, '&'), description: () => doc.value?.excerpt })
const isHome = computed(() => props.path === '/')
const terms = computed(() => (doc.value?.taxonomies?.category ?? []).map((s) => term('category', s)).filter(Boolean))
</script>
<template>
  <div v-if="doc && doc.wide" class="wide-wrap"><div class="floating"><EditorEditLink :path="path" /></div><div class="prose wide"><ContentRenderer :value="doc" /></div></div>
  <div v-else-if="doc" class="container pad" :class="{ 'with-aside': doc.type === 'post' }">
  <article class="page">
    <header v-if="!isHome">
      <p class="editrow"><EditorEditLink :path="path" /></p>
      <h1 v-html="doc.title" />
      <p v-if="doc.type === 'post'" class="meta">
        <time :datetime="doc.date">{{ formatDate(doc.date) }}</time>
        <BaseTag v-for="c in terms" :key="c!.to" :to="c!.to">{{ c!.name }}</BaseTag>
      </p>
    </header>
    <div class="prose"><ContentRenderer :value="doc" /></div>
    <footer v-if="doc.type === 'post'" class="foot"><TermLines :taxonomies="doc.taxonomies" :max-tags="20" /></footer>
  </article>
  <RecentPosts v-if="doc.type === 'post'" />
  </div>
</template>
<style scoped>
.editrow { margin: 0; min-height: 1.6rem; }
.wide-wrap { position: relative; }
.floating { position: absolute; top: var(--space-2); right: var(--space-3); z-index: 5; }
.pad { padding-block: var(--space-4) var(--space-6); }
.with-aside { display: grid; grid-template-columns: 1fr 18rem; gap: var(--space-5); align-items: start; }
.page { max-width: 46rem; margin-inline: auto; width: 100%; }
.with-aside .page { margin-inline: 0; max-width: none; }
h1 { font-size: clamp(2rem, 4.5vw, 3.6rem); margin-top: var(--space-3); }
.foot { margin-top: var(--space-5); padding-top: var(--space-3); border-top: var(--border); }
@media (max-width: 1000px) { .with-aside { grid-template-columns: 1fr; } }
.meta { display: flex; gap: var(--space-3); align-items: center; color: var(--color-text-muted); font-size: var(--step--1); }
</style>
