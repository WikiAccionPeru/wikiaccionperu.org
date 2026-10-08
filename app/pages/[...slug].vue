<script setup lang="ts">
definePageMeta({
  key: (route) => route.fullPath,
  // Listings (news, archives, resource/partner indexes) use the lilac "band" layout.
  middleware: (to) => {
    const parts = [to.params.slug ?? []].flat().filter(Boolean) as string[]
    const listing = parts[0] === 'noticias' || (['recursos', 'alianza'].includes(parts[0]) && (parts.length === 1 || (parts.length === 3 && parts[1] === 'page'))) || !!useSite().archive(parts)
    if (listing) setPageLayout('band')
  },
})
const route = useRoute()
const parts = [route.params.slug ?? []].flat().filter(Boolean) as string[]
const { archive } = useSite()
const path = '/' + parts.join('/')

const news = parts[0] === 'noticias' && (parts.length === 1 || (parts[1] === 'page' && parts.length === 3))
const page = news && parts.length === 3 ? Number(parts[2]) : 1
const arch = !news ? archive(parts) : undefined
const typeArchives: Record<string, { type: string; title: string }> = {
  recursos: { type: 'recurso', title: 'Recursos' },
  alianza: { type: 'alianza', title: 'Alianzas' },
}
const taPaged = parts.length === 3 && parts[1] === 'page' && /^\d+$/.test(parts[2])
const ta = parts.length === 1 || taPaged ? typeArchives[parts[0]] : undefined
const taPage = taPaged ? Number(parts[2]) : 1
const archBase = arch ? `/${parts[0]}/${parts[1]}/` : ''
useSeoMeta({ title: () => (news ? 'Noticias' : arch ? arch.name : ta ? ta.title : 'WikiAcción Perú') + ' — WikiAcción Perú' })
</script>
<template>
  <div v-if="news" class="with-aside">
    <div><h1 class="sr-only">Noticias</h1><NewsList :page="page" base="/noticias/" /></div>
    <RecentPosts />
  </div>
  <div v-else-if="arch" class="with-aside">
    <div><h1>{{ arch.name }}</h1><NewsList :page="arch.page" :base="archBase" :paths="arch.paths" /></div>
    <RecentPosts />
  </div>
  <div v-else-if="ta" class="with-aside">
    <div><h1>{{ ta.title }}</h1><NewsList :page="taPage" :base="`/${parts[0]}/`" :type="ta.type" /></div>
    <RecentPosts />
  </div>
  <ContentPage v-else :path="path" />
</template>
<style scoped>
.with-aside { display: grid; grid-template-columns: 1fr 18rem; gap: var(--space-4); align-items: start; }
h1 { margin-top: 0; }
@media (max-width: 1000px) { .with-aside { grid-template-columns: 1fr; } }
</style>
