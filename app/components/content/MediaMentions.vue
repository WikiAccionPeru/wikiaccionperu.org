<script setup lang="ts">
import all from '~~/data/medios.json'
const props = defineProps<{ perPage?: number | string }>()
const per = Number(props.perPage ?? 8)
const page = ref(1)
const pages = Math.ceil(all.length / per)
const items = computed(() => all.slice((page.value - 1) * per, page.value * per))
const icon = (k: string) => (k === 'video' ? '/media/2025/09/icon_video-e1756883291767.png' : '/media/2025/09/icon_news_2.png')
</script>
<template>
  <div>
    <ul class="grid">
      <li v-for="m in items" :key="m.nota_id" class="item">
        <a :href="m.url" target="_blank" rel="noopener"><NuxtImg :src="icon(m.kind)" alt="" width="96" height="96" loading="lazy" /></a>
        <h3><a :href="m.url" target="_blank" rel="noopener">{{ m.title }}</a></h3>
        <p>{{ m.excerpt }}</p>
        <a :href="m.url" target="_blank" rel="noopener" class="more">Leer más</a>
      </li>
    </ul>
    <nav v-if="pages > 1" class="pager" aria-label="Paginación">
      <button :disabled="page === 1" @click="page--">« Anterior</button>
      <span>{{ page }} / {{ pages }}</span>
      <button :disabled="page === pages" @click="page++">Siguiente »</button>
    </nav>
  </div>
</template>
<style scoped>
.grid { list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr)); gap: var(--space-4); }
.item { background: var(--color-bg-soft); border-radius: var(--radius); padding: var(--space-4); }
h3 { font-size: var(--step-0); margin: var(--space-3) 0 var(--space-2); }
.pager { display: flex; justify-content: center; gap: var(--space-3); margin-top: var(--space-4); }
</style>
