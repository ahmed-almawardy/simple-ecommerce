<script setup lang="ts">
import type { Product } from '~/composables/useShop'
const props = defineProps<{ product: Product; index?: number }>()
const shop = useShop()
const adding = ref(false)
async function addItem() {
  adding.value = true
  await shop.addToCart(props.product)
  adding.value = false
}
</script>

<template>
  <article class="product-card">
    <NuxtLink :to="`/products/${product.slug}`" class="product-image-wrap">
      <img :src="product.image_url" :alt="product.name" class="product-image" loading="lazy" />
      <span v-if="product.is_featured" class="product-tag">NOVA PICK</span>
      <span class="product-open" aria-hidden="true">↗</span>
    </NuxtLink>
    <div class="product-meta">
      <div><p class="product-category">{{ product.category }}</p><NuxtLink :to="`/products/${product.slug}`" class="product-name">{{ product.name }}</NuxtLink></div>
      <span class="product-price">{{ shop.formatPrice(product.price_cents) }}</span>
    </div>
    <button class="quick-add" :disabled="product.stock < 1 || adding" @click="addItem">{{ product.stock < 1 ? 'SOLD OUT' : adding ? 'ADDING…' : 'ADD TO CART +' }}</button>
  </article>
</template>
