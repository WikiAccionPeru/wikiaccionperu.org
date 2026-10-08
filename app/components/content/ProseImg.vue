<script setup lang="ts">
const props = defineProps<{ src?: string; alt?: string; title?: string; width?: string | number; height?: string | number }>()
const local = computed(() => props.src?.startsWith('/media/'))
</script>
<template>
  <figure v-if="local" class="fig">
    <NuxtImg :src="src" :alt="alt ?? ''" :width="width" :height="height" sizes="sm:100vw md:720px lg:720px" loading="lazy" />
    <figcaption v-if="title">{{ title }}</figcaption>
  </figure>
  <img v-else :src="src" :alt="alt ?? ''" :title="title" loading="lazy">
</template>
<style scoped>
.fig { margin: var(--space-4) 0; text-align: center; }
.fig img { max-height: 70vh; width: auto; max-width: 100%; }
figcaption { font-size: var(--step--1); color: var(--color-text-muted); }
</style>
