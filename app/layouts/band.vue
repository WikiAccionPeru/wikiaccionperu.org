<template>
  <div class="shell">
    <AdminBar />
    <SiteHeader />
    <main class="band"><div class="container inner"><slot /></div></main>
    <SiteFooter />
  </div>
</template>
<style scoped>
.shell { min-height: 100vh; display: flex; flex-direction: column; }
.band { flex: 1; background: var(--color-lilac); padding-block: var(--space-5) var(--space-6); }
.inner { width: min(100% - 2rem, var(--container)); }
</style>
