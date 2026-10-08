<script setup lang="ts">
defineProps<{ items: { icon: string; title: string; text: string; to: string }[] }>()
const icons: Record<string, string> = {
  training: 'M12 3l9 4.5-9 4.5-9-4.5zM6 11v4c0 1.7 2.7 3 6 3s6-1.3 6-3v-4',
  meet: 'M4 20v-9l8-6 8 6v9M9 20v-6h6v6',
  contest: 'M12 3l2.5 5 5.5.8-4 3.9.9 5.5-4.9-2.6-4.9 2.6.9-5.5-4-3.9 5.5-.8z',
  library: 'M4 6h16v4H4zM6 10v9h12v-9M10 14h4',
}
</script>
<template>
  <section class="features">
    <NuxtLink v-for="f in items" :key="f.to" :to="f.to" class="feature">
      <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path :d="icons[f.icon]" /></svg>
      <h2>{{ f.title }}</h2>
      <p>{{ f.text }}</p>
      <span class="more">Conocer más »</span>
    </NuxtLink>
  </section>
</template>
<style scoped>
.features { display: grid; grid-template-columns: repeat(4, 1fr); border-bottom: var(--border); }
.feature { display: flex; flex-direction: column; gap: var(--space-2); padding: var(--space-5) var(--space-4); border-left: var(--border); color: inherit; text-decoration: none; }
.feature:first-child { border-left: 0; }
.feature:hover { background: #eee; }
h2 { margin: var(--space-2) 0 0; font-size: 2rem; }
p { margin: 0; font-size: 0.875rem; flex: 1; }
.more { font-weight: 600; text-transform: uppercase; font-size: 0.8rem; margin-top: var(--space-3); }
@media (max-width: 900px) { .features { grid-template-columns: 1fr 1fr; } .feature:nth-child(3) { border-left: 0; } .feature:nth-child(n+3) { border-top: var(--border); } }
@media (max-width: 560px) { .features { grid-template-columns: 1fr; } .feature { border-left: 0; border-top: var(--border); } .feature:first-child { border-top: 0; } }
</style>
