<script setup lang="ts">
const props = defineProps<{ src: string; title?: string }>()
// Privacy: use youtube-nocookie for YouTube embeds.
const url = computed(() => props.src.replace('www.youtube.com/embed', 'www.youtube-nocookie.com/embed'))
</script>
<template>
  <div class="embed"><iframe :src="url" :title="title ?? 'Contenido incrustado'" loading="lazy" allowfullscreen referrerpolicy="strict-origin-when-cross-origin" /></div>
</template>
<style scoped>
.embed { aspect-ratio: 16 / 9; margin: var(--space-4) 0; }
iframe { width: 100%; height: 100%; border: 0; }
</style>
