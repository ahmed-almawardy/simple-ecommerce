<script setup lang="ts">
const shop = useShop()
const { cartCount, notice } = shop
const route = useRoute()
const menuOpen = ref(false)

onMounted(() => shop.initialize())
watch(() => route.fullPath, () => { menuOpen.value = false })
</script>

<template>
  <div class="app-shell">
    <div class="announcement-bar">SMARTER HOME. BETTER EVERYDAY. <span>—</span> DISCOVER THE NOVA EDIT</div>
    <header class="site-header">
      <NuxtLink to="/" class="wordmark" aria-label="NOVA Home and Tech home">NOVA<span class="wordmark-dot">.</span></NuxtLink>
      <button class="mobile-menu-button" aria-label="Toggle menu" @click="menuOpen = !menuOpen">{{ menuOpen ? 'CLOSE' : 'MENU' }}</button>
      <nav class="main-nav" :class="{ 'nav-open': menuOpen }">
        <NuxtLink to="/products?category=Phones%20%26%20Computing">PHONES & COMPUTING</NuxtLink>
        <NuxtLink to="/products?category=Major%20Appliances">HOME APPLIANCES</NuxtLink>
        <NuxtLink to="/products?category=Kitchen%20Appliances">KITCHEN</NuxtLink>
        <NuxtLink to="/products?category=TV%20%26%20Audio">TV & AUDIO</NuxtLink>
      </nav>
      <div class="header-actions">
        <NuxtLink to="/products" class="header-search" aria-label="Search products"><span class="search-glyph">⌕</span><span>Search</span></NuxtLink>
        <NuxtLink to="/account" class="icon-link" aria-label="Account"><span>♙</span></NuxtLink>
        <NuxtLink to="/cart" class="bag-link" aria-label="Shopping cart"><span>▱</span><span class="bag-count">{{ cartCount }}</span></NuxtLink>
      </div>
    </header>
    <div v-if="notice" class="toast" role="status">{{ notice }}</div>
    <main><NuxtPage /></main>
    <footer class="site-footer">
      <div class="footer-top">
        <div><NuxtLink to="/" class="wordmark footer-wordmark">NOVA<span class="wordmark-dot">.</span></NuxtLink><p>Smart choices for better living.</p></div>
        <div class="footer-links"><NuxtLink to="/products">Shop all</NuxtLink><NuxtLink to="/account">My account</NuxtLink><NuxtLink to="/cart">Your cart</NuxtLink></div>
        <div class="footer-newsletter"><span class="eyebrow">THE NOVA LETTER</span><p>New products, smart ideas and better ways to live.</p><NuxtLink to="/auth/register" class="text-link">JOIN THE LIST ↗</NuxtLink></div>
      </div>
      <div class="footer-bottom"><span>© {{ new Date().getFullYear() }} NOVA HOME + TECH</span><span>MADE FOR EVERYDAY LIVING.</span><span>PRIVACY · TERMS</span></div>
    </footer>
  </div>
</template>
