<script setup lang="ts">
import type { Product } from '~/composables/useShop'
const route = useRoute()
const shop = useShop()
const product = ref<Product | null>(null)
const related = ref<Product[]>([])
const loading = ref(true)
const errorMessage = ref('')
const adding = ref(false)

async function loadProduct() {
  loading.value = true
  errorMessage.value = ''
  try {
    product.value = await shop.api<Product>(`/products/${encodeURIComponent(String(route.params.slug))}`)
    if (product.value) {
      const others = await shop.api<Product[]>(`/products?category=${encodeURIComponent(product.value.category)}&limit=4`)
      related.value = others.filter((item) => item.id !== product.value?.id).slice(0, 3)
    }
  } catch (error: any) {
    errorMessage.value = error?.data?.detail || 'Could not load this product. Check that the API is running.'
  } finally { loading.value = false }
}
async function addItem() {
  if (!product.value) return
  adding.value = true
  await shop.addToCart(product.value)
  adding.value = false
}
onMounted(async () => { await shop.initialize(); await loadProduct() })
watch(() => route.params.slug, () => { if (import.meta.client) loadProduct() })
</script>

<template>
  <div>
    <div v-if="loading" class="page-head"><p class="loading-text">Loading product details…</p></div>
    <div v-else-if="errorMessage || !product" class="page-head"><div class="breadcrumb"><NuxtLink to="/products">THE STORE</NuxtLink></div><h1 class="page-title">Product not found.</h1><p class="page-subtitle">{{ errorMessage || 'This product may have moved.' }}</p><NuxtLink to="/products" class="button" style="margin-top:22px">BACK TO THE SHOP ↗</NuxtLink></div>
    <template v-else>
      <div class="page-head" style="padding-bottom:22px"><div class="breadcrumb"><NuxtLink to="/">HOME</NuxtLink> &nbsp;/&nbsp; <NuxtLink to="/products">SHOP</NuxtLink> &nbsp;/&nbsp; {{ product.category.toUpperCase() }}</div></div>
      <section class="product-detail">
        <div class="detail-image"><img :src="product.image_url" :alt="product.name" fetchpriority="high" /></div>
        <div class="detail-info"><div class="detail-category">{{ product.category }} · NOVA HOME + TECH</div><h1 class="detail-title">{{ product.name }}</h1><p class="detail-price">{{ shop.formatPrice(product.price_cents) }}</p><p class="detail-description">{{ product.description }}</p><div class="detail-stock"><span class="stock-dot" :style="{ background: product.stock > 0 ? '#7b9b28' : '#a33' }"></span>{{ product.stock > 0 ? 'In stock — ready to ship' : 'Currently sold out' }}</div><button class="button detail-add" :disabled="product.stock < 1 || adding" @click="addItem">{{ adding ? 'ADDING TO CART…' : 'ADD TO CART' }} <span>↗</span></button><div class="detail-points"><div class="detail-point"><span>DESIGNED FOR EVERYDAY USE</span><span>01 /</span></div><div class="detail-point"><span>SECURE CHECKOUT</span><span>02 /</span></div><div class="detail-point"><span>NEED A HAND?</span><span>SUPPORT ↗</span></div></div></div>
      </section>
      <section v-if="related.length" class="section" style="padding-top:25px"><div class="section-head"><div><div class="eyebrow">KEEP EXPLORING</div><h2 class="section-title" style="margin-top:12px">You may also like.</h2></div><NuxtLink :to="`/products?category=${encodeURIComponent(product.category)}`" class="text-link">VIEW CATEGORY ↗</NuxtLink></div><div class="product-grid"><ProductCard v-for="item in related" :key="item.id" :product="item" /></div></section>
    </template>
  </div>
</template>
