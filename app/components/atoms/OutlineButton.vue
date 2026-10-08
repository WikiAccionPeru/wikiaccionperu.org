<script setup lang="ts">
defineProps<{ to: string; external?: boolean }>()
</script>
<template>
  <NuxtLink :to="to" class="obtn" :target="external ? '_blank' : undefined" :rel="external ? 'noopener' : undefined">
    <slot /> <span aria-hidden="true">»</span>
  </NuxtLink>
</template>
<style scoped>
.obtn { display: inline-block; padding: 4px; border: 1px solid var(--color-line); border-inline: 0; font: 600 0.875rem/1.3 var(--font-body); text-transform: uppercase; text-decoration: none; color: var(--color-text); background: transparent; }
.obtn:hover, .obtn:focus-visible { background: #000; color: #fff; }
</style>
