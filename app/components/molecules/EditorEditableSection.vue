<script setup lang="ts">
defineProps<{ section: string; path?: string }>()
const { me, loaded, refresh } = useAuth()
onMounted(() => { if (!loaded.value) refresh() })
</script>
<template>
  <div class="es">
    <slot />
    <NuxtLink v-if="me.admin" class="pen" :to="{ path: '/admin/edit/', query: { path: path ?? '/', section } }" :title="`Editar esta sección (${section})`" :aria-label="`Editar la sección ${section}`">✎</NuxtLink>
  </div>
</template>
<style scoped>
.es { position: relative; }
.pen { position: absolute; top: 8px; right: 8px; z-index: 8; width: 2rem; height: 2rem; display: grid; place-items: center; border: 1px solid #000; background: var(--color-accent-lilac); color: #000; text-decoration: none; font-size: 1rem; }
.pen:hover { background: #000; color: #fff; }
</style>
