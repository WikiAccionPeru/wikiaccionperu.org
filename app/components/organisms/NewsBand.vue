<script setup lang="ts">
const { thumb, formatDate } = useSite()
const { data } = await useAsyncData('home-news', () =>
  queryCollection('content').where('status', '=', 'publish').where('type', '=', 'post').order('date', 'DESC').select('path', 'title', 'date', 'featured_media').limit(4).all(),
)
</script>
<template>
  <section class="band">
    <div class="container">
      <h2>Noticias</h2>
      <ul class="cards">
        <li v-for="p in data" :key="p.path" class="card">
          <NuxtLink :to="p.path + '/'" class="img" tabindex="-1" aria-hidden="true">
            <NuxtImg v-if="thumb(p.featured_media)" :src="thumb(p.featured_media)" alt="" width="320" height="320" fit="cover" loading="lazy" />
          </NuxtLink>
          <time :datetime="p.date">{{ formatDate(p.date) }}</time>
          <h3><NuxtLink :to="p.path + '/'"><span v-html="p.title" /></NuxtLink></h3>
        </li>
      </ul>
      <p class="more"><OutlineButton to="/noticias/">Ver más noticias</OutlineButton></p>
    </div>
  </section>
</template>
<style scoped>
.band { background: var(--color-lilac); border-bottom: var(--border); padding-block: var(--space-5); }
h2 { margin-top: 0; font-size: 2rem; }
.cards { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-4); }
.card { background: #fff; border: var(--border); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2); }
.img { display: block; aspect-ratio: 1; border: var(--border); overflow: hidden; background: var(--color-bg-soft); }
.img img { width: 100%; height: 100%; object-fit: cover; }
time { font-size: 0.8rem; color: var(--color-text-muted); }
h3 { margin: 0; font-family: var(--font-body); font-weight: 400; font-size: 1.05rem; line-height: 1.35; }
h3 a { text-decoration: none; }
.more { text-align: right; margin: var(--space-4) 0 0; }
@media (max-width: 1000px) { .cards { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 560px) { .cards { grid-template-columns: 1fr; } }
</style>
