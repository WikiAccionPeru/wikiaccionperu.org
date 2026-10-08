<script setup lang="ts">
const props = defineProps<{ page: number; base: string; paths?: string[]; type?: string }>()
const { perPage } = useSite()
const { data } = await useAsyncData(`list-${props.base}-${props.page}`, async () => {
  const q = () => {
    let c = queryCollection('content').where('status', '=', 'publish')
    c = props.paths ? c.where('path', 'IN', props.paths) : c.where('type', '=', props.type ?? 'post')
    return c
  }
  const total = await q().count()
  const items = await q().order('date', 'DESC').select('path', 'title', 'date', 'featured_media', 'taxonomies').limit(perPage).skip((props.page - 1) * perPage).all()
  return { total, items }
})
if (!data.value?.items.length && props.page > 1) throw createError({ statusCode: 404, statusMessage: 'Page not found', fatal: true })
const pages = computed(() => Math.ceil((data.value?.total ?? 0) / perPage))
</script>
<template>
  <section>
    <div class="grid">
      <NewsCard v-for="p in data?.items" :key="p.path" :path="p.path + '/'" :title="p.title" :date="p.date" :featured-media="p.featured_media" :taxonomies="p.taxonomies" />
    </div>
    <PaginationNav :page="page" :pages="pages" :base="base" />
  </section>
</template>
<style scoped>
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-4); }
@media (max-width: 1000px) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
</style>
