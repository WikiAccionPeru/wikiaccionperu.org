<script setup lang="ts">
defineProps<{ title: string; text: string; list: string[]; buttons: { label: string; to: string }[]; image: string; cta: { text: string; label: string; to: string } }>()
</script>
<template>
  <section class="split">
    <div class="copy">
      <h2>{{ title }}</h2>
      <p>{{ text }}</p>
      <ul><li v-for="l in list" :key="l">{{ l }}</li></ul>
      <p class="actions"><OutlineButton v-for="b in buttons" :key="b.label" :to="b.to">{{ b.label }}</OutlineButton></p>
    </div>
    <div class="cta" :style="{ backgroundImage: `linear-gradient(rgba(60,40,110,.55), rgba(60,40,110,.55)), url(${image})` }">
      <p>{{ cta.text }}</p>
      <a :href="cta.to" target="_blank" rel="noopener" class="subscribe">{{ cta.label }} »</a>
    </div>
  </section>
</template>
<style scoped>
.split { display: grid; grid-template-columns: 1.1fr 1fr; border-bottom: var(--border); }
.copy { padding: var(--space-5) clamp(1.5rem, 6vw, 5rem); }
h2 { margin-top: 0; font-size: 1.6rem; }
ul { padding-left: 1.2rem; }
.actions { display: flex; flex-wrap: wrap; gap: var(--space-3); }
.cta { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--space-3); min-height: 320px; background-size: cover; background-position: center; color: #fff; text-align: center; padding: var(--space-5); }
.cta p { margin: 0; white-space: pre-line; }
.subscribe { color: #fff; font: 600 2rem var(--font-heading); text-transform: uppercase; text-decoration: none; }
.subscribe:hover { text-decoration: underline; }
@media (max-width: 768px) { .split { grid-template-columns: 1fr; } }
</style>
