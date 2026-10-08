<script setup lang="ts">
const { data: doc } = await useAsyncData('home', () => queryCollection('content').path('/').first())
const h = computed(() => doc.value?.home)
useSeoMeta({ title: 'WikiAcción Perú — ecología, género y cultura en Wikipedia', description: () => doc.value?.excerpt })
definePageMeta({ layout: 'home' })
</script>
<template>
  <div v-if="h">
    <p class="editfloat"><EditorEditLink path="/" /></p>
    <EditorEditableSection section="hero"><HomeHero v-bind="h.hero" /></EditorEditableSection>
    <EditorEditableSection section="features"><FeatureCards :items="h.features" /></EditorEditableSection>
    <NewsBand />
    <EditorEditableSection section="thematic"><ThematicSplit v-bind="h.thematic" /></EditorEditableSection>
    <MediaBand />
    <section class="partners">
      <div class="container">
        <EditorEditableSection section="partnersTitle"><h2>{{ h.partnersTitle }}</h2></EditorEditableSection>
        <PartnersCarousel />
        <p class="all"><OutlineButton to="/alianza/">Ver todas</OutlineButton></p>
      </div>
    </section>
  </div>
</template>
<style scoped>
.editfloat { position: absolute; right: var(--space-3); margin: var(--space-2) 0 0; z-index: 6; }
.partners { padding-block: var(--space-5); }
h2 { margin-top: 0; font-size: 2rem; }
.all { text-align: center; }
</style>
