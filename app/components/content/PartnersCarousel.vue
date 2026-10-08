<script setup lang="ts">
import featured from '~~/data/partners-featured.json'
const { thumb } = useSite()
const slugs = featured as string[]
const { data } = await useAsyncData('partners-featured', () =>
  queryCollection('content').where('path', 'IN', slugs.map((s) => `/alianza/${s}`)).select('path', 'title', 'featured_media').all(),
)
const items = computed(() =>
  slugs.map((s) => data.value?.find((d) => d.path === `/alianza/${s}`)).filter((d) => !!d).map((d) => ({ ...d!, logo: thumb(d!.featured_media) })),
)
const paused = ref(false)
const duration = computed(() => `${items.value.length * 4}s`)
</script>

<template>
  <section class="partners" aria-label="Organizaciones aliadas" :class="{ paused }">
    <button class="toggle" type="button" :aria-pressed="paused" @click="paused = !paused">
      {{ paused ? '▶ Reanudar' : '⏸ Pausar' }}
    </button>
    <div class="viewport">
      <ul class="track" :style="{ '--duration': duration }">
        <!-- two copies make the loop seamless; the second is hidden from assistive tech -->
        <template v-for="copy in 2" :key="copy">
          <li v-for="p in items" :key="p.path + copy" class="card" :aria-hidden="copy === 2 || undefined">
            <NuxtLink :to="p.path + '/'" :tabindex="copy === 2 ? -1 : undefined" class="logo">
              <NuxtImg v-if="p.logo" :src="p.logo" alt="" width="220" height="140" fit="inside" :loading="copy === 1 ? 'eager' : 'lazy'" />
            </NuxtLink>
            <h3><NuxtLink :to="p.path + '/'" :tabindex="copy === 2 ? -1 : undefined"><span v-html="p.title" /></NuxtLink></h3>
            <NuxtLink :to="p.path + '/'" :tabindex="copy === 2 ? -1 : undefined" class="more">Conocer más »</NuxtLink>
          </li>
        </template>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.partners { position: relative; margin-block: var(--space-4); }
.toggle { margin-bottom: var(--space-2); background: none; border: 1px solid var(--color-border); border-radius: 999px; padding: 0 var(--space-3); font: inherit; font-size: var(--step--1); cursor: pointer; }
.viewport { overflow: hidden; mask-image: linear-gradient(90deg, transparent, #000 4%, #000 96%, transparent); }
.track { --gap: var(--space-4); display: flex; gap: var(--gap); width: max-content; margin: 0; padding: var(--space-2) 0; list-style: none; animation: roll var(--duration) linear infinite; }
.partners:hover .track, .partners:focus-within .track, .paused .track { animation-play-state: paused; }
.card { flex: 0 0 13rem; display: flex; flex-direction: column; align-items: center; text-align: center; gap: var(--space-2); padding: var(--space-3); }
.logo { display: flex; align-items: center; justify-content: center; width: 100%; height: 9rem; }
.logo img { max-width: 100%; max-height: 100%; width: auto; height: auto; object-fit: contain; }
h3 { margin: 0; font-size: 1.05rem; flex: 1; }
h3 a { text-decoration: none; }
.more { font: 600 0.8rem var(--font-body); text-transform: uppercase; text-decoration: none; padding: 4px; border-block: 1px solid #000; color: #000; }
.more:hover { background: #000; color: #fff; }
@keyframes roll { to { transform: translateX(calc(-50% - var(--gap) / 2)); } }
@media (prefers-reduced-motion: reduce) {
  .track { animation: none; width: auto; overflow-x: auto; scroll-snap-type: x mandatory; }
  .card { scroll-snap-align: start; }
  .card[aria-hidden='true'], .toggle { display: none; }
  .viewport { mask-image: none; overflow-x: auto; }
}
</style>
