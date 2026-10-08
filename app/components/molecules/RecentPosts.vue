<script setup lang="ts">
const { data } = await useAsyncData('recent-posts', () => queryCollection('content').where('status', '=', 'publish').where('type', '=', 'post').order('date', 'DESC').select('path', 'title').limit(5).all())
</script>
<template>
  <div class="side">
  <SearchBox />
  <aside class="recent" aria-labelledby="recent-h">
    <h2 id="recent-h">Entradas recientes</h2>
    <ul><li v-for="p in data" :key="p.path"><NuxtLink :to="p.path + '/'"><span v-html="p.title" /></NuxtLink></li></ul>
  </aside>
  </div>
</template>
<style scoped>
.side { display: grid; gap: var(--space-4); }
.recent { background: #fff; border: var(--border); padding: var(--space-3) var(--space-4); }
h2 { margin: 0 0 var(--space-3); font-size: 1.4rem; }
ul { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-3); font-size: 0.8rem; }
a { text-decoration: none; } a:hover { text-decoration: underline; }
</style>
