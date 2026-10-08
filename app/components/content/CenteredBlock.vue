<template><section class="centered"><div class="inner"><slot /></div></section></template>
<style scoped>
.centered { padding: var(--space-6) var(--space-3); text-align: center; }
.inner { max-width: 52rem; margin-inline: auto; font-size: 1.15rem; }
.inner :deep(h2) { font-size: 1.8rem; }
</style>
