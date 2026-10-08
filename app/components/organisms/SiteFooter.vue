<script setup lang="ts">
const commit = useRuntimeConfig().public.commit
const { me, loginUrl } = useAuth()
const route = useRoute()
</script>
<template>
  <footer class="site-footer">
    <div class="container grid">
      <section class="brand">
        <NuxtLink to="/" aria-label="WikiAcción Perú — inicio">
          <NuxtImg src="/media/2024/04/Mesa-de-trabajo-1-copia-2-8.png" alt="WikiAcción Perú" width="300" height="122" loading="lazy" />
        </NuxtLink>
      </section>
      <section>
        <h2>Recursos</h2>
        <p><NuxtLink to="/recurso/manual-de-edicion-en-wikipedia/" class="caps">Manual de edición en Wikipedia</NuxtLink></p>
      </section>
      <section>
        <h2>Contacto</h2>
        <p>wikiaccionperu@gmail.com</p>
        <ul class="social">
          <li><a href="https://www.facebook.com/wikiaccionperu/" rel="me noopener" target="_blank" aria-label="Facebook" style="color:#1877f2"><svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor" aria-hidden="true"><path d="M12 2C6.5 2 2 6.5 2 12c0 5 3.7 9.1 8.4 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.5h-1.3c-1.2 0-1.6.8-1.6 1.6V12h2.8l-.4 2.9h-2.3v7C18.3 21.1 22 17 22 12c0-5.5-4.5-10-10-10z" /></svg></a></li>
          <li><a href="https://www.instagram.com/wikiaccionperu/" rel="me noopener" target="_blank" aria-label="Instagram" style="color:#e1306c"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="17" rx="5" /><circle cx="12" cy="12" r="4" /><circle cx="17" cy="7" r="1" fill="currentColor" stroke="none" /></svg></a></li>
          <li><a href="https://twitter.com/wikiaccionperu" rel="me noopener" target="_blank" aria-label="X / Twitter" style="color:#1da1f2"><svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor" aria-hidden="true"><path d="M22 5.9c-.7.3-1.5.5-2.4.6.9-.5 1.5-1.3 1.8-2.3-.8.5-1.7.8-2.6 1a4.1 4.1 0 0 0-7 3.7A11.6 11.6 0 0 1 3.4 4.6a4.1 4.1 0 0 0 1.3 5.5c-.7 0-1.3-.2-1.9-.5 0 2 1.4 3.7 3.3 4.1-.6.2-1.2.2-1.8.1.5 1.600 2 2.800 3.800 2.800A8.300 8.300 0 0 1 2 18.300 11.700 11.700 0 0 0 8.300 20c7.500 0 11.700-6.300 11.700-11.700v-.5c.8-.6 1.500-1.300 2-2z" /></svg></a></li>
          <li><a href="https://www.youtube.com/channel/UCj0ozdMU66P_6oZ2jLtD5nA" rel="me noopener" target="_blank" aria-label="YouTube" style="color:#ff0000"><svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor" aria-hidden="true"><path d="M21.6 7.2a2.500 2.500 0 0 0-1.800-1.800C18.200 5 12 5 12 5s-6.200 0-7.800.4A2.500 2.500 0 0 0 2.400 7.200C2 8.800 2 12 2 12s0 3.200.4 4.800a2.500 2.500 0 0 0 1.800 1.800C5.800 19 12 19 12 19s6.200 0 7.800-.4a2.500 2.500 0 0 0 1.800-1.800c.4-1.600.4-4.800.4-4.800s0-3.200-.4-4.800zM10 15V9l5.200 3z" /></svg></a></li>
        </ul>
      </section>
      <section class="license">
        <a rel="license" href="https://creativecommons.org/licenses/by-sa/4.0/deed.es"><img src="/cc-by-sa-4.0.png" alt="Licencia Creative Commons Atribución-CompartirIgual 4.0" width="88" height="31"></a>
        <p>Excepto donde se indique lo contrario, el contenido de este sitio está bajo una licencia Creative Commons Atribución-CompartirIgual 4.0</p>
        <p class="small"><a v-if="!me.user" :href="loginUrl(route.fullPath)" rel="nofollow">Acceso editores</a><template v-if="!me.user"> · </template><NuxtLink to="/styleguide/">Guía de estilo</NuxtLink> · versión <code>{{ commit }}</code></p>
      </section>
    </div>
  </footer>
</template>
<style scoped>
.site-footer { border-top: var(--border); background: #fff; padding-block: var(--space-5); }
.grid { display: grid; grid-template-columns: 1.3fr 1fr 1fr 1fr; gap: var(--space-5); align-items: start; }
.brand img { width: min(100%, 260px); height: auto; }
h2 { margin: 0 0 var(--space-3); font: 400 1rem var(--font-heading); }
p { margin: 0 0 var(--space-3); font-size: 0.8rem; }
.caps { text-transform: uppercase; text-decoration: none; }
.caps:hover { text-decoration: underline; }
.social { list-style: none; display: flex; gap: var(--space-3); padding: 0; margin: 0; }
.license p { font-size: 0.72rem; margin-top: var(--space-3); }
.small { color: var(--color-text-muted); }
@media (max-width: 900px) { .grid { grid-template-columns: 1fr 1fr; } }
@media (max-width: 560px) { .grid { grid-template-columns: 1fr; } }
</style>
