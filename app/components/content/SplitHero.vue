<script setup lang="ts">
defineProps<{ image: string; color?: 'lilac' | 'green' | 'blue'; alt?: string }>()
</script>
<template>
  <section class="split" :class="color ?? 'lilac'">
    <div class="copy"><slot /></div>
    <div class="photo"><NuxtImg :src="image" :alt="alt ?? ''" width="1024" height="768" fit="cover" sizes="sm:100vw lg:50vw" /></div>
  </section>
</template>
<style scoped>
.split { display: grid; grid-template-columns: 1fr 1fr; border-bottom: var(--border); }
.lilac { background: var(--color-lilac); } .green { background: var(--color-green); } .blue { background: var(--color-blue); }
.copy { padding: var(--space-5) clamp(1.5rem, 4vw, 3.5rem); }
.copy :deep(h1), .copy :deep(h2) { margin-top: 0; font-size: 2.2rem; }
.copy :deep(p) { font-size: 1.1rem; }
.photo { position: relative; min-height: 320px; }
.photo img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
@media (max-width: 768px) { .split { grid-template-columns: 1fr; } .photo { order: -1; } }
</style>
