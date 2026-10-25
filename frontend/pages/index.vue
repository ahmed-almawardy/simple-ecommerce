<script setup lang="ts">
import type { Product } from '~/composables/useShop'
const shop = useShop()
const featured = ref<Product[]>([])
const loading = ref(true)
onMounted(async () => {
  await shop.initialize()
  try { featured.value = await shop.api<Product[]>('/products?featured=true&limit=4') }
  catch { featured.value = [] }
  finally { loading.value = false }
})
</script>

<template>
  <div>
    <section class="hero">
      <div class="hero-copy">
        <div class="hero-kicker">HOME, APPLIANCES & EVERYDAY TECH</div>
        <h1 class="hero-title">Make room<br>for <em>better.</em></h1>
        <p class="hero-description">Thoughtful appliances and smart technology for the way you live. From kitchen essentials to your next screen, find the upgrades that make every day work better.</p>
        <div class="hero-actions"><NuxtLink to="/products" class="button">SHOP ALL PRODUCTS <span>↗</span></NuxtLink><NuxtLink to="/products?category=Major%20Appliances" class="button button-outline">EXPLORE HOME APPLIANCES</NuxtLink></div>
        <div class="hero-footnote">SMARTER CHOICES · BETTER EVERYDAY LIVING</div>
      </div>
      <div class="hero-art">
        <img src="https://images.unsplash.com/photo-1761656630581-69a58e4e1c09?auto=format&fit=crop&w=1500&q=90" alt="Modern kitchen designed for everyday home living" fetchpriority="high" />
        <div class="hero-burst">LIVE<br>SMARTER<br><span>✳</span></div>
        <div class="hero-number">NOVA EDIT — THE EVERYDAY UPGRADE</div>
      </div>
    </section>

    <div class="ticker"><div class="ticker-track"><span>TECH THAT FITS YOUR LIFE <i>✳</i></span><span>BETTER HOME, EVERY DAY <i>✳</i></span><span>MADE FOR REAL LIVING <i>✳</i></span><span>TECH THAT FITS YOUR LIFE <i>✳</i></span></div></div>

    <section class="section">
      <div class="section-head"><div><div class="eyebrow">THE NOVA EDIT</div><h2 class="section-title" style="margin-top:12px">Upgrade your everyday.</h2><p class="section-note">Useful technology, trusted essentials and modern appliances in one place.</p></div><NuxtLink to="/products" class="text-link">SHOP ALL PRODUCTS ↗</NuxtLink></div>
      <div v-if="loading" class="loading-text">Loading products…</div>
      <div v-else-if="featured.length" class="product-grid"><ProductCard v-for="(product, index) in featured" :key="product.id" :product="product" :index="index" /></div>
      <div v-else class="empty-state"><p class="eyebrow">YOUR STORE IS GETTING READY</p><h2>Products are waiting.</h2><p class="section-note" style="margin:0 auto 20px">Start the FastAPI server to load the demo catalogue.</p><NuxtLink to="/products" class="button">EXPLORE THE STORE ↗</NuxtLink></div>
    </section>

    <section class="split-feature">
      <div class="split-image"><img src="https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=1400&q=85" alt="Large-screen television in a modern living room" loading="lazy" /></div>
      <div class="split-copy"><div class="eyebrow">THE RIGHT UPGRADE CHANGES EVERYTHING</div><h2>Small details. Smarter living.</h2><p>From kitchen machines and laundry essentials to entertainment, laptops and wearables, discover practical technology picked for your home and your routine.</p><NuxtLink to="/products?category=TV%20%26%20Audio" class="button">EXPLORE TV & AUDIO <span>↗</span></NuxtLink></div>
    </section>

    <section class="section">
      <div class="section-head"><div><div class="eyebrow">FIND WHAT YOU NEED</div><h2 class="section-title" style="margin-top:12px">Shop by category.</h2><p class="section-note">Explore big home upgrades, kitchen helpers and the tech you take everywhere.</p></div></div>
      <div class="category-grid">
        <NuxtLink to="/products?category=Major%20Appliances" class="category-card"><img src="https://images.unsplash.com/photo-1587785580224-ff32e30978de?auto=format&fit=crop&w=1000&q=85" alt="Home laundry appliance" loading="lazy" /><div><h3>Major Appliances</h3><span>UPGRADE YOUR HOME ↗</span></div></NuxtLink>
        <NuxtLink to="/products?category=Kitchen%20Appliances" class="category-card"><img src="https://images.unsplash.com/photo-1556912172-45b7abe8b7e1?auto=format&fit=crop&w=1000&q=85" alt="Modern kitchen and countertop appliances" loading="lazy" /><div><h3>Kitchen Appliances</h3><span>MAKE EVERYDAY EASIER ↗</span></div></NuxtLink>
        <NuxtLink to="/products?category=TV%20%26%20Audio" class="category-card"><img src="https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=1000&q=85" alt="Television in a living room" loading="lazy" /><div><h3>TV & Audio</h3><span>BRING IT TO LIFE ↗</span></div></NuxtLink>
        <NuxtLink to="/products?category=Phones%20%26%20Computing" class="category-card"><img src="https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=1000&q=85" alt="Laptop computer on a desk" loading="lazy" /><div><h3>Phones & Computing</h3><span>WORK, CREATE, CONNECT ↗</span></div></NuxtLink>
        <NuxtLink to="/products?category=Watches%20%26%20Wearables" class="category-card"><img src="https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=1000&q=85" alt="Smartwatch and wearable technology" loading="lazy" /><div><h3>Watches & Wearables</h3><span>YOUR DAY AT A GLANCE ↗</span></div></NuxtLink>
        <NuxtLink to="/products?category=Smart%20Home" class="category-card"><img src="https://images.unsplash.com/photo-1558002038-1055907df827?auto=format&fit=crop&w=1000&q=85" alt="Smart home device in a modern interior" loading="lazy" /><div><h3>Smart Home</h3><span>MAKE HOME WORK SMARTER ↗</span></div></NuxtLink>
      </div>
    </section>

    <section class="quote-section"><span>THE NOVA POINT OF VIEW</span><p>“The best technology isn't about more stuff. It's about making everyday life feel a little easier.”</p><span>HOME + TECH · CURATED FOR YOU</span></section>
  </div>
</template>
