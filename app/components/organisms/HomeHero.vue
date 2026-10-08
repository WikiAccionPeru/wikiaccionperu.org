<script setup lang="ts">
defineProps<{ kicker: string; title: string; text: string; image: string; buttons: { label: string; to: string }[] }>()
</script>
<template>
  <section class="hero">
    <div class="copy">
      <p class="kicker">{{ kicker }}</p>
      <h1>{{ title }}</h1>
      <p class="lead">{{ text }}</p>
      <p class="actions"><OutlineButton v-for="b in buttons" :key="b.to" :to="b.to">{{ b.label }}</OutlineButton></p>
    </div>
    <div class="photo"><NuxtImg :src="image" alt="" width="1024" height="720" fit="cover" sizes="sm:100vw lg:50vw" /></div>
  </section>
</template>
<style scoped>
.hero { display: grid; grid-template-columns: 1fr 1fr; min-height: 720px; background: var(--color-green); border-bottom: var(--border); }
.copy { display: flex; flex-direction: column; justify-content: center; padding: var(--space-5) clamp(1.5rem, 7vw, 6.5rem); }
.kicker { margin: 0; font-weight: 600; text-transform: uppercase; font-size: 0.875rem; }
h1 { margin: 0 0 var(--space-3); font-size: clamp(2.2rem, 4vw, 3.25rem); }
.lead { font-size: 1.1rem; max-width: 34rem; }
.actions { display: flex; flex-wrap: wrap; gap: var(--space-3); margin: var(--space-4) 0 0; }
.photo { position: relative; min-height: 280px; }
.photo img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
@media (max-width: 768px) { .hero { grid-template-columns: 1fr; } .photo { order: -1; min-height: 240px; } }
</style>
